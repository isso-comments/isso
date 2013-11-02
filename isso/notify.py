# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from smtplib import SMTP, SMTP_SSL
from email.header import Header
from email.mime.text import MIMEText


def format(comment, permalink, remote_addr, deletion_key, activation_key=None):

    rv = []
    rv.append("%s schrieb:" % (comment["author"] or "Jemand"))
    rv.append("")
    rv.append(comment["text"])
    rv.append("")

    if comment["website"]:
        rv.append("Webseite des Kommentators: %s" % comment["website"])

    rv.append("IP Adresse: %s" % remote_addr)
    rv.append("Link zum Kommentar: %s" % permalink)

    rv.append("")
    rv.append("---")
    rv.append("Kommentar löschen: %s" % deletion_key)

    if activation_key:
        rv.append("Kommentar freischalten: %s" % activation_key)

    return u'\n'.join(rv)


class Connection(object):
    """
    Establish connection to SMTP server, optional with authentication, and
    close connection afterwards.
    """

    def __init__(self, conf):
        self.conf = conf

    def __enter__(self):
        self.server = (SMTP_SSL if self.conf.getboolean('smtp', 'ssl') else SMTP)(
            host=self.conf.get('smtp', 'host'), port=self.conf.getint('smtp', 'port'))

        if self.conf.get('smtp', 'username') and self.conf.get('smtp', 'password'):
            self.server.login(self.conf.get('smtp', 'username'),
                              self.conf.get('smtp', 'password'))

        return self.server

    def __exit__(self, exc_type, exc_value, traceback):
        self.server.quit()


class SMTPMailer(object):

    def __init__(self, conf):

        self.conf = conf
        self.from_addr = conf.get('smtp', 'from')
        self.to_addr = conf.get('smtp', 'to')

        # test SMTP connectivity
        with Connection(self.conf):
            pass

    def sendmail(self, subject, body):

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = "Ich schrei sonst! <%s>" % self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = Header(subject, 'utf-8')

        with Connection(self.conf) as con:
            con.sendmail(self.from_addr, self.to_addr, msg.as_string())


class NullMailer(object):

    def sendmail(self, subject, body):
        pass
