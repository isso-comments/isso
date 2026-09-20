# -*- encoding: utf-8 -*-

import io
import json
import hashlib
import hmac
import smtplib
import socket
import time

from _thread import start_new_thread
from configparser import NoOptionError
from email.message import EmailMessage
from email.utils import formatdate
from urllib.parse import quote
from urllib.request import Request, urlopen

import logging

logger = logging.getLogger("isso")

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso import local


def create_comment_action_url(uri, action, key):
    return uri + "/" + action + "/" + key


class SMTPConnection(object):
    def __init__(self, conf):
        self.conf = conf

    def __enter__(self):
        klass = smtplib.SMTP_SSL if self.conf.get("security") == "ssl" else smtplib.SMTP
        self.client = klass(host=self.conf.get("host"), port=self.conf.getint("port"), timeout=self.conf.getint("timeout"))

        if self.conf.get("security") == "starttls":
            import ssl

            self.client.starttls(context=ssl.create_default_context())

        username = self.conf.get("username")
        password = self.conf.get("password")
        if username and password:
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
        try:
            self.thread_notify = isso.conf.getboolean("general", "thread-notifications")
        except NoOptionError:
            self.thread_notify = False

        # test SMTP connectivity
        try:
            with SMTPConnection(self.conf):
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            logger.exception("unable to connect to SMTP server")

        if uwsgi:

            def spooler(args):
                try:
                    self._sendmail(
                        args[b"subject"].decode("utf-8"),
                        args["body"].decode("utf-8"),
                        args[b"to"].decode("utf-8"),
                        args[b"headers"].decode("utf-8"),
                    )
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __iter__(self):
        yield "comments.new:after-save", self.notify_new
        yield "comments.activate", self.notify_activated

    def unsubscribe_url(self, comment_id, recipient, thread_wide=False):
        """
        Link to stop notifications for :param:`recipient`. By default it
        covers comment :param:`comment_id` and its replies; with
        :param:`thread_wide` it covers the whole thread.
        """
        uri = self.public_endpoint + "/id/%i" % comment_id
        payload = ("unsubscribe", recipient, "thread") if thread_wide else ("unsubscribe", recipient)
        key = self.isso.sign(payload)
        return uri + "/unsubscribe/" + quote(recipient) + "/" + key

    def format(self, thread, comment, admin=False, unsubscribe_url=None):
        rv = io.StringIO()

        author = comment["author"] or "Anonymous"
        if admin and comment["email"]:
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
        rv.write("---\n")

        if admin:
            uri = self.public_endpoint + "/id/%i" % comment["id"]
            key = self.isso.sign(comment["id"])

            rv.write("Delete comment: %s\n" % create_comment_action_url(uri, "delete", key))

            if comment["mode"] == 2:
                rv.write("Activate comment: %s\n" % create_comment_action_url(uri, "activate", key))

        else:
            rv.write("Unsubscribe from this conversation: %s\n" % unsubscribe_url)

        rv.seek(0)
        return rv.read()

    def notify_new(self, thread, comment):
        if self.admin_notify:
            body = self.format(thread, comment, admin=True)
            subject = "New comment posted"
            if thread["title"]:
                subject = "%s on %s" % (subject, thread["title"])
            self.sendmail(subject, body, thread, comment, None)

        if comment["mode"] == 1:
            self.notify_users(thread, comment)

    def notify_activated(self, thread, comment):
        self.notify_users(thread, comment)

    def subscribers(self, thread, comment, thread_subscribers):
        """
        Yield ``(comment, is_reply)`` pairs for every comment whose author may
        want to know about :param:`comment`. Reply subscribers come first, so
        that somebody subscribed to both gets the reply wording.
        """
        if self.reply_notify and comment.get("parent") is not None:
            parent_comment = self.isso.db.comments.get(comment["parent"])
            if parent_comment is not None:
                yield parent_comment, True
            for sibling in self.isso.db.comments.fetch(thread["uri"], mode=1, parent=comment["parent"]):
                yield sibling, True

        for other in thread_subscribers:
            yield other, False

    def notify_users(self, thread, comment):
        # Notify interested authors that a new comment is posted
        notified = set()
        thread_subscribers = self.isso.db.comments.thread_subscribers(thread["id"]) if self.thread_notify else []
        # a reply link would also cancel the thread-wide subscription, so
        # thread subscribers always get the thread-wide link
        thread_subscriptions = {}
        for subscriber in thread_subscribers:
            thread_subscriptions.setdefault(subscriber["email"], subscriber["id"])

        for comment_to_notify, is_reply in self.subscribers(thread, comment, thread_subscribers):
            email = comment_to_notify["email"]
            if (
                not email
                or not comment_to_notify["notification"]
                or email in notified
                or comment_to_notify["id"] == comment["id"]
                or email == comment["email"]
            ):
                continue

            if email in thread_subscriptions:
                unsubscribe_url = self.unsubscribe_url(thread_subscriptions[email], email, thread_wide=True)
            else:
                # same link as before thread notifications existed: covers
                # the parent comment and all replies to it
                unsubscribe_url = self.unsubscribe_url(comment["parent"], email)

            if is_reply:
                subject = "Re: New comment posted on %s" % thread["title"]
            else:
                subject = "New comment posted on %s" % thread["title"]

            body = self.format(thread, comment, unsubscribe_url=unsubscribe_url)
            headers = (("List-Unsubscribe", unsubscribe_url),)
            self.sendmail(subject, body, thread, comment, to=email, headers=headers)
            notified.add(email)

    def sendmail(self, subject, body, thread, comment, to=None, headers=None):
        to = to or self.conf.get("to")
        if not subject:
            # Fallback, just in case as an empty subject does not work
            subject = "isso notification"

        if uwsgi:
            if not headers:
                headers = ""
            uwsgi.spool(
                {
                    b"subject": subject.encode("utf-8"),
                    b"body": body.encode("utf-8"),
                    b"to": to.encode("utf-8"),
                    b"headers": headers.encode("utf-8"),
                }
            )
        else:
            start_new_thread(self._retry, (subject, body, to, headers))

    def _sendmail(self, subject, body, to_addr, headers=None):
        from_addr = self.conf.get("from")

        msg = EmailMessage()
        msg.set_payload(body, "utf-8")
        msg["From"] = from_addr
        msg["To"] = to_addr
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject

        for key, val in headers if headers else ():
            msg.add_header(key, val)

        with SMTPConnection(self.conf) as con:
            con.send_message(msg, from_addr, to_addr)

    def _retry(self, subject, body, to, headers):
        for x in range(5):
            try:
                self._sendmail(subject, body, to, headers)
            except smtplib.SMTPConnectError:
                time.sleep(60)
            else:
                break


class Webhook(object):
    def __init__(self, isso):
        self.conf = isso.conf.section("webhook")
        self.urls = list(self.conf.getiter("url"))
        self.secret = self.conf.get("secret")
        self.timeout = self.conf.getint("timeout")

        if not self.urls:
            logger.warning("webhook notifications are enabled without webhook URLs")

    def __iter__(self):
        yield "comments.new:after-save", self.notify_new

    def notify_new(self, thread, comment):
        if not self.urls:
            return

        payload = {
            "event": "comment.created",
            "thread": {key: thread[key] for key in ("id", "uri", "title")},
            "comment": {
                key: comment[key] for key in ("id", "parent", "created", "modified", "mode", "text", "author", "website")
            },
        }
        start_new_thread(self.send, (payload,))

    def send(self, payload):
        body = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        headers = {"Content-Type": "application/json", "X-Isso-Event": payload["event"]}
        if self.secret:
            digest = hmac.new(self.secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
            headers["X-Isso-Signature"] = "sha256=" + digest

        for url in self.urls:
            request = Request(url, data=body, headers=headers, method="POST")
            try:
                with urlopen(request, timeout=self.timeout):
                    pass
            except Exception:
                logger.exception("unable to deliver comment webhook to %s", url)


class Stdout(object):
    def __init__(self, isso):
        self.isso = isso
        self.public_endpoint = isso.conf.get("server", "public-endpoint") or local("host")

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
        logger.info("Link to comment: %s" % (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))

        uri = self.public_endpoint + "/id/%i" % comment["id"]
        key = self.isso.sign(comment["id"])

        logger.info("Delete comment: %s" % create_comment_action_url(uri, "delete", key))

        if comment["mode"] == 2:
            logger.info("Activate comment: %s" % create_comment_action_url(uri, "activate", key))

    def _edit_comment(self, comment):
        logger.info("comment %i edited: %s", comment["id"], json.dumps(comment))

    def _delete_comment(self, id):
        logger.info("comment %i deleted", id)

    def _activate_comment(self, thread, comment):
        logger.info("comment %(id)s activated" % thread)
