# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import sys
import io
import time
import json
import copy

import socket
import smtplib

from email.utils import formatdate
from email.header import Header
from email.mime.text import MIMEText
from email import encoders

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


def _format(thread, comment, general_host, key):
    rv = io.StringIO()

    author = comment["author"] or "Anonymous"
    if comment["email"]:
        author += " <%s>" % comment["email"]

    rv.write(author + " wrote:\n")
    rv.write("\n")
    rv.write(comment["text"] + "\n")
    rv.write("\n")

    if comment["website"]:
        rv.write("User's URL: %s\n" % comment["website"])

    rv.write("IP address: %s\n" % comment["remote_addr"])
    rv.write("Link to comment: %s\n" %
             (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
    rv.write("\n")

    uri = general_host + "/id/%i" % comment["id"]
#    key = self.isso.sign(comment["id"])

    rv.write("---\n")
    rv.write("Delete comment: %s\n" % (uri + "/delete/" + key))

    if comment["mode"] == 2:
        rv.write("Activate comment: %s\n" % (uri + "/activate/" + key))

    rv.seek(0)
    return rv.read()
    
    
class SMTP(object):

    def __init__(self, isso):

        self.isso = isso
        self.conf = isso.conf.section("smtp")
        gh = isso.conf.get("general", "host")
        if type(gh) == str:
            self.general_host = gh
        #if gh is not a string then gh is a list
        else:
            self.general_host = gh[0]

        # test SMTP connectivity
        try:
            with self:
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            logger.exception("unable to connect to SMTP server")

        if uwsgi:
            def spooler(args):
                try:
                    self._sendmail(args[b"subject"].decode("utf-8"),
                                   args["body"].decode("utf-8"))
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __enter__(self):
        klass = (smtplib.SMTP_SSL if self.conf.get(
            'security') == 'ssl' else smtplib.SMTP)
        self.client = klass(host=self.conf.get('host'),
                            port=self.conf.getint('port'),
                            timeout=self.conf.getint('timeout'))

        if self.conf.get('security') == 'starttls':
            if sys.version_info >= (3, 4):
                import ssl
                self.client.starttls(context=ssl.create_default_context())
            else:
                self.client.starttls()

        username = self.conf.get('username')
        password = self.conf.get('password')
        if username and password:
            if PY2K:
                username = username.encode('ascii')
                password = password.encode('ascii')

            self.client.login(username, password)

        return self.client

    def __exit__(self, exc_type, exc_value, traceback):
        self.client.quit()

    def __iter__(self):
        yield "comments.new:after-save", self.notify

    def format(self, thread, comment):
        rv = io.StringIO()

        author = comment["author"] or "Anonymous"
        if comment["email"]:
            author += " <%s>" % comment["email"]

        rv.write(author + " wrote:\n")
        rv.write("\n")
        rv.write(comment["text"] + "\n")
        rv.write("\n")

        if comment["website"]:
            rv.write("User's URL: %s\n" % comment["website"])

        rv.write("IP address: %s\n" % comment["remote_addr"])
        rv.write("Link to comment: %s\n" %
                 (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
        rv.write("\n")

        uri = self.general_host + "/id/%i" % comment["id"]
        key = self.isso.sign(comment["id"])

        rv.write("---\n")
        rv.write("Delete comment: %s\n" % (uri + "/delete/" + key))

        if comment["mode"] == 2:
            rv.write("Activate comment: %s\n" % (uri + "/activate/" + key))

        rv.seek(0)
        return rv.read()

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
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
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

        yield "comments.new:after-save", self._new_comment_after_save
        yield "comments.edit", self._edit_comment
        yield "comments.new:new-thread", self._new_thread
        yield "comments.new:finish", self._new_comment_finish
        yield "comments.delete", self._delete_comment
        yield "comments.activate", self._activate_comment

    def _new_comment_after_save(self, thread, comment):
        c = copy.copy(comment)
        if 'voters' in c:
            del c['voters']
        logger.info("comments.new:after-save: %s, %s",
                    json.dumps(thread), json.dumps(c))

    def _edit_comment(self, comment):
        c = copy.copy(comment)
        if 'voters' in c:
            del c['voters']
        logger.info('comments,edit: %s, %s',
                    json.dumps(thread), json.dumps(c))


    def _new_thread(self, thread):
        logger.info("comments.new:new-thread %(id)s: %(title)s" % thread)

    def _new_comment_finish(self, thread, comment):
        c = copy.copy(comment)
        if 'voters' in c:
            del c['voters']
        logger.info("comments.new:finish: %s, %s",
                    json.dumps(thread), json.dumps(c))

    def _delete_comment(self, id):
        logger.info("comments.delete %i ", id)

    def _activate_comment(self, id):
        logger.info("comments.activate %s" % id)


import subprocess

class Syscall(object):

    def __init__(self, isso):
        self.isso = isso
        self.conf = isso.conf.section("syscall")
        gh = isso.conf.get("general", "host")
        if type(gh) == str:
            self.general_host = gh
        #if gh is not a string then gh is a list
        else:
            self.general_host = gh[0]

    def __iter__(self):
        yield "comments.new:after-save", self._new_comment_after_save
        yield "comments.edit", self._edit_comment

    def _new_comment_after_save(self, thread, comment):
        key=self.isso.sign(comment["id"])
        msgbody=_format(thread,comment,self.general_host,key)
        subject = "..." + thread['uri'][-15:] + " :: " + comment['text'][:15] + "..."
        cmdlist = [ a.replace('{{SUBJECT}}',subject,1) for a in self.conf.getiter('call') ]
        logger.info(cmdlist);
        p=subprocess.run(cmdlist,
                         input=str(msgbody).encode(),
                         stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE)
        s = "Syscall: return code " + str(p.returncode) + "\n" \
        + "stdout:\n" \
        + str(p.stdout) + "\n" \
        + "stderr:\n" \
        + str(p.stderr) + "\n"
        if p.returncode != 0:
            logger.error(s)
        else:
            logger.info(s)

    def _edit_comment(self, comment):
        pass
    
