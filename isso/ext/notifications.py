# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import sys
import io
import time
import json

import socket
import smtplib

from email.utils import formatdate
from email.header import Header
from email.mime.text import MIMEText

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

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


class SMTPConnection(object):

    def __init__(self, conf):
        self.conf = conf

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


class SMTP(object):

    def __init__(self, isso):

        self.isso = isso
        self.conf = isso.conf.section("smtp")
        self.public_endpoint = isso.conf.get("server", "public-endpoint") or local("host")
        self.admin_notify = any((n in ("smtp", "SMTP")) for n in isso.conf.getlist("general", "notify"))
        self.reply_notify = isso.conf.getboolean("general", "reply-notifications")

        # test SMTP connectivity
        try:
            with SMTPConnection(self.conf):
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            logger.exception("unable to connect to SMTP server")

        if uwsgi:
            def spooler(args):
                try:
                    self._sendmail(args[b"subject"].decode("utf-8"),
                                   args["body"].decode("utf-8"),
                                   args[b"to"].decode("utf-8"))
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __iter__(self):
        yield "comments.new:after-save", self.notify_new
        yield "comments.activate", self.notify_activated

    def format(self, thread, comment, parent_comment, recipient=None, admin=False):

        rv = io.StringIO()

        author = comment["author"] or "Anonymous"
        if comment["email"]:
            author += " <%s>" % comment["email"]

        if admin:
            uri = self.public_endpoint + "/id/%i" % comment["id"]
            key = self.isso.sign(comment["id"])
            try:
                if comment["mode"] == 2:
                    if comment["website"]:
                        con_for=self.isso.conf.getlist("smtp", "admin_format_urluser_moderate")
                        con_for="\n".join(con_for)
                        rv.write(con_for.format(author=author,
                                                comment=comment["text"],
                                                website=comment["website"],
                                                ip=comment["remote_addr"],
                                                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                                                del_link=uri + "/delete/" + key,
                                                act_link=uri + "/activate/" + key)
                        )
                    else:
                        con_for=self.isso.conf.getlist("smtp", "admin_format_nourluser_moderate")
                        con_for="\n".join(con_for)
                        rv.write(con_for.format(author=author,
                                                comment=comment["text"],
                                                ip=comment["remote_addr"],
                                                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                                                del_link=uri + "/delete/" + key,
                                                act_link=uri + "/activate/" + key)
                        )
                else:
                    if comment["website"]:
                        con_for=self.isso.conf.getlist("smtp", "admin_format_urluser_direct")
                        con_for="\n".join(con_for)
                        rv.write(con_for.format(author=author,
                                                comment=comment["text"],
                                                website=comment["website"],
                                                ip=comment["remote_addr"],
                                                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                                                del_link=uri + "/delete/" + key)
                        )
                    else:
                        con_for=self.isso.conf.getlist("smtp", "admin_format_nourluser_direct")
                        con_for="\n".join(con_for)
                        rv.write(con_for.format(author=author,
                                                comment=comment["text"],
                                                ip=comment["remote_addr"],
                                                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                                                del_link=uri + "/delete/" + key)
                        )
            except:
                con_for=[]
                con_for.append("{author} wrote:\n\n{comment}\n".format(author=author,comment=comment["text"]))
                if comment["website"]:
                    con_for.append("User's URL: %s" % comment["website"])
                con_for.append("IP address: %s" % comment["remote_addr"])
                con_for.append("Link to comment: %s\n" %
                               (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
                con_for.append("---")
                con_for.append("Delete comment: %s" % (uri + "/delete/" + key))
                if comment["mode"] == 2:
                    con_for.append("Activate comment: %s" % (uri + "/activate/" + key))
                rv.write("\n".join(con_for))
 

        else:
            uri = self.public_endpoint + "/id/%i" % parent_comment["id"]
            key = self.isso.sign(('unsubscribe', recipient))
            try:
                con_for=self.isso.conf.getlist("smtp", "user_format");
                con_for="\n".join(con_for)
                rv.write(con_for.format(author=author,
                                        comment=comment["text"],
                                        link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                                        unsubscribe=uri + "/unsubscribe/" + quote(recipient) + "/" + key))
            except:
                con_for=[]
                con_for.append("{author} wrote:\n\n{comment}\n".format(author=author,comment=comment["text"]))
                con_for.append("Link to comment: %s\n" %
                               (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
                con_for.append("---")
                con_for.append("Unsubscribe from this conversation: %s\n" % (uri + "/unsubscribe/" + quote(recipient) + "/" + key))
                rv.write("\n".join(con_for))

        rv.seek(0)
        return rv.read()

    def notify_new(self, thread, comment):
        if self.admin_notify:
            body = self.format(thread, comment, None, admin=True)
            self.sendmail(thread["title"], body, thread, comment)

        if comment["mode"] == 1:
            self.notify_users(thread, comment)

    def notify_activated(self, thread, comment):
        self.notify_users(thread, comment)

    def notify_users(self, thread, comment):
        if self.reply_notify and "parent" in comment and comment["parent"] is not None:
            # Notify interested authors that a new comment is posted
            notified = []
            parent_comment = self.isso.db.comments.get(comment["parent"])
            comments_to_notify = [parent_comment] if parent_comment is not None else []
            comments_to_notify += self.isso.db.comments.fetch(thread["uri"], mode=1, parent=comment["parent"])
            for comment_to_notify in comments_to_notify:
                email = comment_to_notify["email"]
                if "email" in comment_to_notify and comment_to_notify["notification"] and email not in notified \
                        and comment_to_notify["id"] != comment["id"] and email != comment["email"]:
                    body = self.format(thread, comment, parent_comment, email, admin=False)
                    subject = "Re: New comment posted on %s" % thread["title"]
                    self.sendmail(subject, body, thread, comment, to=email)
                    notified.append(email)

    def sendmail(self, subject, body, thread, comment, to=None):
        to = to or self.conf.get("to")
        if uwsgi:
            uwsgi.spool({b"subject": subject.encode("utf-8"),
                         b"body": body.encode("utf-8"),
                         b"to": to.encode("utf-8")})
        else:
            start_new_thread(self._retry, (subject, body, to))

    def _sendmail(self, subject, body, to_addr):

        from_addr = self.conf.get("from")

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(subject, 'utf-8')

        with SMTPConnection(self.conf) as con:
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
        logger.info('comment %i edited: %s',
                    comment["id"], json.dumps(comment))

    def _delete_comment(self, id):
        logger.info('comment %i deleted', id)

    def _activate_comment(self, thread, comment):
        logger.info("comment %(id)s activated" % thread)
