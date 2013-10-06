# -*- encoding: utf-8 -*-

from __future__ import print_function

import io
import os
import time

import thread
import threading

import socket
import smtplib

from ConfigParser import ConfigParser

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso import notify, colors

class Config:

    default = [
        "[general]",
        "dbpath = /tmp/isso.db", "secretkey = %r" % os.urandom(24),
        "host = http://localhost:8080/", "passphrase = p@$$w0rd",
        "max_age = 450",
        "[server]",
        "host = localhost", "port = 8080", "reload = off",
        "[SMTP]",
        "username = ", "password = ",
        "host = localhost", "port = 465", "ssl = on",
        "to = ", "from = "
    ]

    @classmethod
    def load(cls, configfile):

        rv = ConfigParser(allow_no_value=True)
        rv.readfp(io.StringIO(u'\n'.join(Config.default)))

        if configfile:
            rv.read(configfile)

        return rv


def threaded(func):

    def dec(self, *args, **kwargs):
        thread.start_new_thread(func, (self, ) + args, kwargs)

    return dec


class NaiveMixin(object):

    def __init__(self, conf):

        try:
             print(" * connecting to SMTP server", end=" ")
             mailer = notify.SMTPMailer(conf)
             print("[%s]" % colors.green("ok"))
        except (socket.error, smtplib.SMTPException):
             print("[%s]" % colors.red("failed"))
             mailer = notify.NullMailer()

        self.mailer = mailer
        self.lock = threading.Lock()

    @threaded
    def notify(self, subject, body, retries=5):

        for x in range(retries):
            try:
                self.mailer.sendmail(subject, body)
            except Exception:
                time.sleep(60)
            else:
                break


class uWSGIMixin(NaiveMixin):

    def __init__(self, conf):
        super(uWSGIMixin, self).__init__(conf)

        class Lock():

            def __enter__(self):
                while uwsgi.queue_get(0) == "LOCK":
                    time.sleep(0.1)

                uwsgi.queue_set(uwsgi.queue_slot(), "LOCK")

            def __exit__(self, exc_type, exc_val, exc_tb):
                uwsgi.queue_pop()

        def spooler(args):
            try:
                self.mailer.sendmail(args["subject"].decode('utf-8'), args["body"].decode('utf-8'))
            except smtplib.SMTPConnectError:
                return uwsgi.SPOOL_RETRY
            else:
                return uwsgi.SPOOL_OK

        self.lock = Lock()
        uwsgi.spooler = spooler

    def notify(self, subject, body, retries=5):
        uwsgi.spool({"subject": subject.encode('utf-8'), "body": body.encode('utf-8')})
