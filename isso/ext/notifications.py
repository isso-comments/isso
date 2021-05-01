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

from pathlib import Path
from string import Template
from urllib.parse import quote

import logging

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso import dist, local
from isso.views.comments import isurl

from _thread import start_new_thread

from requests import HTTPError, Session

# Globals
logger = logging.getLogger("isso")


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
            import ssl
            self.client.starttls(context=ssl.create_default_context())

        username = self.conf.get('username')
        password = self.conf.get('password')
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

        rv.write("Link to comment: %s\n" %
                 (local("origin") + thread["uri"] + "#isso-%i" % comment["id"]))
        rv.write("\n")
        rv.write("---\n")

        if admin:
            uri = self.public_endpoint + "/id/%i" % comment["id"]
            key = self.isso.sign(comment["id"])

            rv.write("Delete comment: %s\n" % (uri + "/delete/" + key))

            if comment["mode"] == 2:
                rv.write("Activate comment: %s\n" % (uri + "/activate/" + key))

        else:
            uri = self.public_endpoint + "/id/%i" % parent_comment["id"]
            key = self.isso.sign(('unsubscribe', recipient))

            rv.write("Unsubscribe from this conversation: %s\n" % (uri + "/unsubscribe/" + quote(recipient) + "/" + key))

        rv.seek(0)
        return rv.read()

    def notify_new(self, thread, comment):
        if self.admin_notify:
            body = self.format(thread, comment, None, admin=True)
            subject = "New comment posted"
            if thread['title']:
                subject = "%s on %s" % (subject, thread["title"])
            self.sendmail(subject, body, thread, comment)

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
        if not subject:
            # Fallback, just in case as an empty subject does not work
            subject = 'isso notification'
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


class WebHook(object):
    """Notification handler for web hook.

    :param isso_instance: Isso application instance. Used to get moderation key.
    :type isso_instance: object

    :raises ValueError: if the provided URL is not valid
    :raises FileExistsError: if the provided JSON template doesn't exist
    :raises TypeError: if the provided template file is not a JSON
    """

    def __init__(self, isso_instance: object):
        """Instanciate class."""
        # store isso instance
        self.isso_instance = isso_instance
        # retrieve relevant configuration
        self.public_endpoint = isso_instance.conf.get(
            section="server", option="public-endpoint"
        ) or local("host")
        webhook_conf_section = isso_instance.conf.section("webhook")
        self.wh_url = webhook_conf_section.get("url")
        self.wh_template = webhook_conf_section.get("template")

        # check required settings
        if not isurl(self.wh_url):
            raise ValueError(
                "Web hook requires a valid URL. "
                "The provided one is not correct: {}".format(self.wh_url)
            )

        # check optional template
        if not len(self.wh_template):
            self.wh_template = None
            logger.debug("No template provided.")
        elif not Path(self.wh_template).is_file():
            raise FileExistsError(
                "Invalid web hook template path: {}".format(self.wh_template)
            )
        elif not Path(self.wh_template).suffix == ".json":
            raise TypeError()(
                "Template must be a JSON file: {}".format(self.wh_template)
            )
        else:
            self.wh_template = Path(self.wh_template)

    def __iter__(self):

        yield "comments.new:after-save", self.new_comment

    def new_comment(self, thread: dict, comment: dict) -> bool:
        """Triggered when a new comment is saved.

        :param thread: comment thread
        :type thread: dict
        :param comment: comment object
        :type comment: dict

        :return: True if eveythring went fine. False if not.
        :rtype: bool
        """

        try:
            # get moderation URLs
            moderation_urls = self.moderation_urls(thread, comment)

            if self.wh_template:
                post_data = self.render_template(thread, comment, moderation_urls)
            else:
                post_data = {
                    "author_name": comment.get("author", "Anonymous"),
                    "author_email": comment.get("email"),
                    "author_website": comment.get("website"),
                    "comment_ip_address": comment.get("remote_addr"),
                    "comment_text": comment.get("text"),
                    "comment_url_activate": moderation_urls[0],
                    "comment_url_delete": moderation_urls[1],
                    "comment_url_view": moderation_urls[2],
                }

            self.send(post_data)
        except Exception as err:
            logger.error(err)
            return False

        return True

    def moderation_urls(self, thread: dict, comment: dict) -> tuple:
        """Helper to build comment related URLs (deletion, activation, etc.).

        :param thread: comment thread
        :type thread: dict
        :param comment: comment object
        :type comment: dict

        :return: tuple of URS in alpha order (activate, admin, delete, view)
        :rtype: tuple
        """
        uri = "{}/id/{}".format(self.public_endpoint, comment.get("id"))
        key = self.isso_instance.sign(comment.get("id"))

        url_activate = "{}/activate/{}".format(uri, key)
        url_delete = "{}/delete/{}".format(uri, key)
        url_view = "{}#isso-{}".format(
            local("origin") + thread.get("uri"), comment.get("id")
        )

        return url_activate, url_delete, url_view

    def render_template(
        self, thread: dict, comment: dict, moderation_urls: tuple
    ) -> str:
        """Format comment information as webhook payload filling the specified template.

        :param thread: isso thread
        :type thread: dict
        :param comment: isso comment
        :type comment: dict
        :param moderation_urls: comment moderation URLs
        :type comment: tuple

        :return: formatted message from template
        :rtype: str
        """
        # load template
        with self.wh_template.open("r") as in_file:
            tpl_json_data = json.load(in_file)
        tpl_str = Template(json.dumps(tpl_json_data))

        # substitute
        out_msg = tpl_str.substitute(
            AUTHOR_NAME=comment.get("author", "Anonymous"),
            AUTHOR_EMAIL="<{}>".format(comment.get("email", "")),
            AUTHOR_WEBSITE=comment.get("website", ""),
            COMMENT_IP_ADDRESS=comment.get("remote_addr"),
            COMMENT_TEXT=comment.get("text"),
            COMMENT_URL_ACTIVATE=moderation_urls[0],
            COMMENT_URL_DELETE=moderation_urls[1],
            COMMENT_URL_VIEW=moderation_urls[2],
        )

        return out_msg

    def send(self, structured_msg: str) -> bool:
        """Send the structured message as a notification to the class webhook URL.

        :param str structured_msg: structured message to send

        :rtype: bool
        """
        with Session() as requests_session:

            # send requests
            response = requests_session.post(
                url=self.wh_url,
                data=structured_msg,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "Isso/{0} (+https://posativ.org/isso)".format(
                        dist.version
                    ),
                },
            )

            try:
                response.raise_for_status()
                logger.info("Web hook sent to %s" % self.wh_url)
            except HTTPError as err:
                logger.error(
                    "Something went wrong during POST request to the web hook. Trace: %s"
                    % err
                )
                return False

        # if no error occurred
        return True
