# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import sys
import smtplib

from email.utils import formatdate
from email.header import Header
from email.mime.text import MIMEText

from . import Task


class Send(Task):

    def __init__(self, section):
        self.conf = section
        self.client = None

    def __enter__(self):
        klass = (smtplib.SMTP_SSL if self.conf.get('security') == 'ssl' else smtplib.SMTP)
        self.client = klass(host=self.conf.get('host'),
                            port=self.conf.getint('port'),
                            timeout=self.conf.getint('timeout'))

        if self.conf.get('security') == 'starttls':
            if sys.version_info >= (3, 4):
                import ssl
                self.client.starttls(context=ssl.create_default_context())
            else:
                self.client.starttls()

        if self.conf.get('username') and self.conf.get('password'):
            self.client.login(self.conf.get('username'),
                              self.conf.get('password'))

        return self.client

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client is not None:
            self.client.quit()
            self.client = None

    def run(self, data):
        subject = data["subject"]
        body = data["body"]

        from_addr = self.conf.get("from")
        to_addr = self.conf.get("to")

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = from_addr
        msg['To'] = to_addr
        msg['Date'] = formatdate(localtime=True)
        msg['Subject'] = Header(subject, 'utf-8')

        with self as con:
            con.sendmail(from_addr, to_addr, msg.as_string())
