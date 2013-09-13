
import time
import logging

from smtplib import SMTP, SMTP_SSL, SMTPException
from email.mime.text import MIMEText


def create(comment, subject, permalink, remote_addr):

    rv = []
    rv.append("%s schrieb:" % (comment["author"] or "Jemand"))
    rv.append("")
    rv.append(comment["text"])
    rv.append("")

    if comment["website"]:
        rv.append("Webseite des Kommentators: %s" % comment["website"])

    rv.append("IP Adresse: %s" % remote_addr)
    rv.append("Link zum Kommentar: %s" % permalink)

    return subject, u'\n'.join(rv)


class SMTPMailer(object):

    def __init__(self, conf):

        self.server = (SMTP_SSL if conf.getboolean('SMTP', 'ssl') else SMTP)(
            host=conf.get('SMTP', 'host'), port=conf.getint('SMTP', 'port'))

        if conf.get('SMTP', 'username') and conf.get('SMTP', 'password'):
            self.server.login(conf.get('SMTP', 'username'), conf.get('SMTP', 'password'))

        self.from_addr = conf.get('SMTP', 'from')
        self.to_addr = conf.get('SMTP', 'to')

    def sendmail(self, subject, body, retries=5):

        msg = MIMEText(body, 'plain', 'utf-8')
        msg['From'] = "Ich schrei sonst! <%s>" % self.from_addr
        msg['To'] = self.to_addr
        msg['Subject'] = subject.encode('utf-8')

        for i in range(retries):
            try:
                self.server.sendmail(self.from_addr, self.to_addr, msg.as_string())
            except SMTPException:
                logging.exception("uncaught exception, %i of %i:", i + 1, retries)
            else:
                return

            time.sleep(60)


class NullMailer(object):

    def sendmail(self, subject, body, retries=5):
        pass
