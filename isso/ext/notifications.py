# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import sys
import time
import json
import os.path

import socket
import smtplib

from email.utils import formatdate
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from jinja2 import Environment, FileSystemLoader
import jinja2.exceptions as jinja2_exceptions
from translate import Translator

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
from isso import local, dist
from isso.utils import html

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
        self.mail_lang = self.isso.conf.get("mail", "language")
        self.mail_format = self.isso.conf.get("mail", "format")

        try:
            self.no_name = Translator(to_lang=self.mail_lang).translate("Anonymous")
        except Exception as err:
            logger.warn("[mail] Some error about translate. %s"
                        % type(err)
                        )
            for er in err.args:
                logger.warn("      %s" % er)
            self.no_name = "Anonymous"
            logger.warn('[mail] Anonymous fell back to "Anonymous".')
        else:
            if self.mail_lang.upper() in self.no_name:
                self.no_name = "Anonymous"
                logger.warn('[mail] No anonymous found for %s, anonymous fell back to "Anonymous".'
                            % self.mail_lang)

        # test SMTP connectivity
        try:
            with SMTPConnection(self.conf):
                logger.info("connected to SMTP server")
        except (socket.error, smtplib.SMTPException):
            if os.path.join(dist.location, "isso", "tests", "test_mail.py") in sys.argv:
                pass
            else:
                logger.exception("unable to connect to SMTP server")

        if uwsgi:
            def spooler(args):
                try:
                    self._sendmail(args[b"subject"].decode("utf-8"),
                                   args[b"to"].decode("utf-8"),
                                   body=args["body"].decode("utf-8"),
                                   body_html=args["body_html"].decode("utf-8"),
                                   body_plain=args["body_plain"].decode("utf-8"))
                except smtplib.SMTPConnectError:
                    return uwsgi.SPOOL_RETRY
                else:
                    return uwsgi.SPOOL_OK

            uwsgi.spooler = spooler

    def __iter__(self):
        yield "comments.new:after-save", self.notify_new
        yield "comments.activate", self.notify_activated

    def format(self, thread, comment, parent_comment, recipient=None, admin=False, part="plain"):
        jinjaenv = Environment(loader=FileSystemLoader("/"))

        temp_path = os.path.join(dist.location, "isso", "templates")
        com_ori = "comment_{0}.{1}".format(self.mail_lang, part)
        com_ori_admin = com_ori_user = "comment.%s" % part

        try:
            jinjaenv.get_template(os.path.join(temp_path, com_ori))
        except jinja2_exceptions.TemplateSyntaxError as err:
            logger.warn("[mail] Wrong format. %s" % err)
            logger.warn("[mail] Default template fell back to the one for en.")
            logger.info("[mail] You can edit the default template for {0} at {1}. The default template you are using now is {2}. ({3} part)".format(
                self.mail_lang,
                os.path.join(temp_path, com_ori),
                os.path.join(temp_path, com_ori_admin),
                part))
        except jinja2_exceptions.TemplateNotFound:
            logger.warn("[mail] No default template for such language: %s. "
                        % self.mail_lang
                        )
            logger.warn("[mail] Default template fell back to the one for en.")
            logger.info("[mail] You can add the default template for {0} as {1}. The default template you are using now is {2}. ({3} part)".format(
                self.mail_lang,
                os.path.join(temp_path, com_ori),
                os.path.join(temp_path, com_ori_admin),
                part))
        except Exception as err:
            logger.warn("[mail] Some error about jinja2. %s"
                        % type(err)
                        )
            for er in err.args:
                logger.warn("      %s" % er)
            logger.warn("[mail] Default template fell back to the one for en.")
            logger.info("[mail] You can edit the default template for {0} at {1}. The default template you are using now is {2}. ({3} part)".format(
                self.mail_lang,
                os.path.join(temp_path, com_ori),
                os.path.join(temp_path, com_ori_admin),
                part))
        else:
            com_ori_admin = com_ori_user = os.path.basename(com_ori)

        if self.isso.conf.get("mail", "template"):
            com_ori = self.isso.conf.get("mail", "template")
            if os.path.isfile(com_ori):
                try:
                    jinjaenv.get_template(com_ori)
                except jinja2_exceptions.TemplateSyntaxError as err:
                    logger.warn("[mail] Wrong format. %s" % err)
                    logger.warn("[mail] The template fell back to the default ({} part)".format(part))
                except Exception as err:
                    logger.warn("[mail] %s" % type(err))
                    for er in err.args:
                        logger.warn("      %s" % er)
                    logger.warn("[mail] The template fell back to the default ({} part)".format(part))
                else:
                    logger.info("[mail] You are now using your customized template {0} for {1} part".format(com_ori, part))
                    com_ori_admin = com_ori_user = os.path.basename(com_ori)
                    temp_path = os.path.dirname(com_ori)
            elif os.path.isdir(com_ori):
                try:
                    jinjaenv.get_template(os.path.join(com_ori, "admin.%s" % part))
                    jinjaenv.get_template(os.path.join(com_ori, "user.%s" % part))
                except jinja2_exceptions.TemplateSyntaxError as err:
                    logger.warn("[mail] Wrong format. %s" % err)
                    logger.warn("[mail] The template fell back to the default ({} part)".format(part))
                except jinja2_exceptions.TemplateNotFound:
                    logger.warn("[mail] No usable templates for {format} part found in {c_path}."
                                .format(
                                    c_path=com_ori,
                                    format=part))
                    logger.warn("[mail] The template used for email notification sent to admin should be named 'admin.{0}', and the template for reply notification to the subcribed users should be named 'user.{0}'."
                                .format(part))
                    logger.warn("[mail] The template fell back to the default (%s part)" % part)
                except Exception as err:
                    logger.warn("[mail] Some error about jinja2. %s" % type(err))
                    for er in err.args:
                        logger.warn("      %s" % er)
                    logger.warn("[mail] The template fell back to the default (%s part)" % part)

                else:
                    logger.info("[mail] You are now using your customized templates in {0} ({1} part), 'admin.{1}' for admin notification, 'user.{1}' for reply notication to the subcribers".format(com_ori, part))
                    com_ori_admin = "admin.%s" % part
                    com_ori_user = "user.%s" % part
                    temp_path = com_ori
            else:
                logger.warn("[mail] %s does not exist. Fell back to the default template for %s."
                            % (com_ori, part))
        else:
            logger.info("[mail] You are now using the default template (%s part)." % part)

        jinjaenv = Environment(loader=FileSystemLoader(temp_path))
        if part == "html":
            convert = html.Markup(self.isso.conf.section("markup")).render
            comment_text = convert(comment["text"])
        else:
            comment_text = comment["text"]

        if admin:
            uri = self.public_endpoint + "/id/%i" % comment["id"]
            self.key = self.isso.sign(comment["id"])
            com_temp = jinjaenv.get_template(com_ori_admin).render(
                author=comment["author"] or self.no_name or "Anonymous",
                email=comment["email"],
                admin=admin,
                mode=comment["mode"],
                comment=comment_text,
                website=comment["website"],
                ip=comment["remote_addr"],
                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                del_link=uri + "/delete/" + self.key,
                act_link=uri + "/activate/" + self.key,
                thread_link=local("origin") + thread["uri"],
                thread_title=thread["title"],
                part=part)
        else:
            uri = self.public_endpoint + "/id/%i" % parent_comment["id"]
            self.key = self.isso.sign(('unsubscribe', recipient))
            com_temp = jinjaenv.get_template(com_ori_user).render(
                author=comment["author"] or self.no_name or "Anonymous",
                email=comment["email"],
                admin=admin,
                comment=comment_text,
                website=comment["website"],
                ip=comment["remote_addr"],
                parent_link=local("origin") + thread["uri"] + "#isso-%i" % parent_comment["id"],
                com_link=local("origin") + thread["uri"] + "#isso-%i" % comment["id"],
                unsubscribe=uri + "/unsubscribe/" + quote(recipient) + "/" + self.key,
                thread_link=local("origin") + thread["uri"],
                thread_title=thread["title"],
                part=part)

        return com_temp

    def notify_new(self, thread, comment):
        if self.admin_notify:
            mailtitle_admin = self.isso.conf.get("mail", "title_admin").format(
                title=thread["title"],
                replier=comment["author"] or self.no_name)
            if self.mail_format == "multipart":
                body_plain = self.format(thread, comment, None, admin=True, part="plain")
                body_html = self.format(thread, comment, None, admin=True, part="html")
                self.sendmail(
                    subject=mailtitle_admin,
                    body_html=body_html,
                    body_plain=body_plain,
                    thread=thread,
                    comment=comment)
            else:
                body = self.format(thread, comment, None, admin=True, part=self.mail_format)
                self.sendmail(
                    subject=mailtitle_admin,
                    body=body,
                    thread=thread,
                    comment=comment)

            logger.info("[mail] Sending notification mail titled '{0}' to the admin".format(mailtitle_admin))

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
                    subject = self.isso.conf.get("mail", "title_user").format(
                        title=thread["title"],
                        receiver=parent_comment["author"] or self.no_name,
                        replier=comment["author"] or self.no_name)
                    if self.mail_format == "multipart":
                        body_plain = self.format(thread, comment, parent_comment, email, admin=False, part="plain")
                        body_html = self.format(thread, comment, parent_comment, email, admin=False, part="html")
                        self.sendmail(
                            subject=subject,
                            body_html=body_html,
                            body_plain=body_plain,
                            thread=thread,
                            comment=comment,
                            to=email)
                    else:
                        body = self.format(thread, comment, parent_comment, email, admin=False, part=self.mail_format)
                        self.sendmail(
                            subject=subject,
                            body=body,
                            thread=thread,
                            comment=comment,
                            to=email)
                    logger.info("[mail] Sending notification mail titled '{0}' to {1}"
                                .format(
                                    subject,
                                    email))
                    notified.append(email)

    def sendmail(self, subject, thread, comment, body=None, body_html=None, body_plain=None, to=None):
        to = to or self.conf.get("to")
        if uwsgi:
            uwsgi.spool({b"subject": subject.encode("utf-8"),
                         b"body": body.encode("utf-8") or Null,
                         b"body_html": body_html or Null,
                         b"body_plain": body_plain or Null,
                         b"to": to.encode("utf-8")})
        else:
            if self.mail_format == "multipart":
                start_new_thread(self._retry, (subject, to, None, body_html, body_plain))
            else:
                start_new_thread(self._retry, (subject, to, body, None, None))

    def _sendmail(self, subject, to_addr, body=None, body_html=None, body_plain=None):

        from_addr = self.conf.get("from")

        if self.mail_format == "multipart":
            msg = MIMEMultipart('alternative')
            msg_plain = MIMEText(body_plain, "plain", 'utf-8')
            msg_html = MIMEText(body_html, "html", 'utf-8')
            msg.attach(msg_plain)
            msg.attach(msg_html)

        msg = MIMEText(body, self.mail_format, 'utf-8')

        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(subject, 'utf-8')

        with SMTPConnection(self.conf) as con:
            con.sendmail(from_addr, to_addr, msg.as_string())

    def _retry(self, subject, to, body=None, body_html=None, body_plain=None):
        for x in range(5):
            try:
                if self.mail_format == "multipart":
                    self._sendmail(
                        subject=subject,
                        body_html=body_html,
                        body_plain=body_plain,
                        to_addr=to)
                else:
                    self._sendmail(
                        subject=subject,
                        body=body,
                        to_addr=to)
            except smtplib.SMTPConnectError:
                logger.info("[mail] The notification mail hasn't been sent to %s due to SMTPConnectError, trying in 1 minute unless no tries left. (Tries so far: %d / 5)" % (to, x + 1))
                time.sleep(60)
            else:
                logger.info("[mail] The notification mail has been sent to %s successfully." % to)
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
