# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import time
import json

import socket
import smtplib

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
            logger.warn("unable to connect to SMTP server")

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
        klass = (smtplib.SMTP_SSL if self.conf.getboolean('ssl') else smtplib.SMTP)
        self.client = klass(host=self.conf.get('host'), port=self.conf.getint('port'))

        if self.conf.get('username') and self.conf.get('password'):
            self.client.login(self.conf.get('username'),
                              self.conf.get('password'))

        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.quit()

    def __iter__(self):
        yield "comments.new:after-save", self.notify

    def format(self, thread, comment):

        permalink = local("origin") + thread["uri"] + "#isso-%i" % comment["id"]

        rv = []
        rv.append("%s schrieb:" % (comment["author"] or "Jemand"))
        rv.append("")
        rv.append(comment["text"])
        rv.append("")

        if comment["website"]:
            rv.append("Webseite des Kommentators: %s" % comment["website"])

        rv.append("IP Adresse: %s" % comment["remote_addr"])
        rv.append("Link zum Kommentar: %s" % permalink)
        rv.append("")

        uri = local("host") + "/id/%i" % comment["id"]
        key = self.isso.sign(comment["id"])

        rv.append("---")
        rv.append("Kommentar löschen: %s" % uri + "/delete/" + key)

        if comment["mode"] == 2:
            rv.append("Kommentar freischalten: %s" % uri + "/activate/" + key)

        return u'\n'.join(rv)

    def notify(self, thread, comment):

        body = self.format(thread, comment)

        if uwsgi:
            uwsgi.spool({b"subject": thread["title"].encode("utf-8"),
                         b"body": body.encode("utf-8")})
        else:
            start_new_thread(self._retry, (thread["title"], body))

    def _sendmail(self, subject, body):

        from_addr = self.conf.get("from")
        to_addr = self.conf.get("to")

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = "Ich schrei sonst! <%s>" % from_addr
        msg['To'] = to_addr
        msg['Subject'] = Header(subject, 'utf-8')

        with self as con:
            con.sendmail(from_addr, to_addr, msg.as_string())

    def _retry(self, subject, body):
        for x in range(5):
            try:
                self._sendmail(subject, body)
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
