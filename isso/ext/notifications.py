# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import io
import time
import json

import socket
import smtplib

from email.utils import formatdate
from email.header import Header
from email.mime.text import MIMEText

import logging
logger = logging.getLogger("isso")

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso.compat import PY2K
from isso import local

if PY2K:
    from thread import start_new_thread
else:
    from _thread import start_new_thread


class SMTP(object):

    def __init__(self, isso):

        self.isso = isso
        self.conf = isso.conf.section("smtp")

        # test SMTP connectivity
        try:
            with self:
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            logger.exception("unable to connect to SMTP server")

        if uwsgi:
            def spooler(args):
                try:
                    self._sendmail(args["subject"].decode("utf-8"),
                                   args["body"].decode("utf-8"))
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __enter__(self):
        klass = (smtplib.SMTP_SSL if self.conf.get('security') == 'ssl' else smtplib.SMTP)
        self.client = klass(host=self.conf.get('host'), port=self.conf.getint('port'))
        if self.conf.get('security') == 'starttls':
            self.client.starttls()

        if self.conf.get('username') and self.conf.get('password'):
            self.client.login(self.conf.get('username'),
                              self.conf.get('password'))

        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.quit()

    def __iter__(self):
        yield "comments.new:after-save", self.notify

    def format(self, thread, comment, admin=False):

        rv = io.StringIO()

        author = comment["author"] or "Anonymous"
        if comment["email"]:
            author += " <%s>" % comment["email"]

        rv.write(author + " wrote:\n")
        rv.write("\n")
        rv.write(comment["text"] + "\n")
        rv.write("\n")

        if admin:
            if comment["website"]:
                rv.write("User's URL: %s\n" % comment["website"])

            rv.write("IP address: %s\n" % comment["remote_addr"])
            rv.write("Link to comment: %s\n" % (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
            rv.write("\n")

            uri = local("host") + "/id/%i" % comment["id"]
            key = self.isso.sign(comment["id"])

            rv.write("---\n")
            rv.write("Delete comment: %s\n" % (uri + "/delete/" + key))

            if comment["mode"] == 2:
                rv.write("Activate comment: %s\n" % (uri + "/activate/" + key))

        rv.seek(0)
        return rv.read()

    def notify(self, thread, comment):
        if "parent" in comment:
            comment_parent = self.isso.db.comments.get(comment["parent"])
            # Notify the author that a new comment is posted if requested
            if "email" in comment_parent and comment_parent["notification"]:
                body = self.format(thread, comment, admin=False)
                subject = "Re: New comment posted on %s" % thread["title"]
                self.sendmail(subject, body, thread, comment, to=comment_parent["email"])

        body = self.format(thread, comment, admin=True)
        self.sendmail(thread["title"], body, thread, comment)

    def sendmail(self, subject, body, thread, comment, to=None):
        if uwsgi:
            uwsgi.spool({b"subject": subject.encode("utf-8"),
                         b"body": body.encode("utf-8"),
                         b"to": to})
        else:
            start_new_thread(self._retry, (subject, body, to))

    def _sendmail(self, subject, body, to=None):

        from_addr = self.conf.get("from")
        to_addr = to or self.conf.get("to")

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = "Ich schrei sonst! <%s>" % from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(subject, 'utf-8')

        with self as con:
            con.sendmail(from_addr, to_addr, msg.as_string())

    def _retry(self, subject, body, to):
        for x in range(5):
            try:
                self._sendmail(subject, body, to)
            except smtplib.SMTPConnectError:
                time.sleep(60)
            else:
                break


class Stdout(object):

    def __init__(self, conf):
        pass

    def __iter__(self):

        yield "comments.new:new-thread", self._new_thread
        yield "comments.new:finish", self._new_comment
        yield "comments.edit", self._edit_comment
        yield "comments.delete", self._delete_comment
        yield "comments.activate", self._activate_comment

    def _new_thread(self, thread):
        logger.info("new thread %(id)s: %(title)s" % thread)

    def _new_comment(self, thread, comment):
        logger.info("comment created: %s", json.dumps(comment))

    def _edit_comment(self, comment):
        logger.info('comment %i edited: %s', comment["id"], json.dumps(comment))

    def _delete_comment(self, id):
        logger.info('comment %i deleted', id)

    def _activate_comment(self, id):
        logger.info("comment %s activated" % id)
