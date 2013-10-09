# -*- encoding: utf-8 -*-

from __future__ import print_function

import io
import os
import time
import binascii

import thread
import threading

import socket
import smtplib

import httplib
import urlparse

from configparser import ConfigParser

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso import notify, colors


class Config:

    default = [
        "[general]",
        "dbpath = /tmp/isso.db", "secretkey = %r" % binascii.b2a_hex(os.urandom(24)),
        "host = http://localhost:8080/", "passphrase = p@$$w0rd",
        "max-age = 900",
        "[server]",
        "host = localhost", "port = 8080", "reload = off",
        "[SMTP]",
        "username = ", "password = ",
        "host = localhost", "port = 465", "ssl = on",
        "to = ", "from = ",
        "[guard]",
        "enabled = on",
        "ratelimit = 2"
        ""
    ]

    @classmethod
    def load(cls, configfile):

        rv = ConfigParser(allow_no_value=True)
        rv.read_file(io.StringIO(u'\n'.join(Config.default)))

        if configfile:
            rv.read(configfile)

        return rv


def threaded(func):

    def dec(self, *args, **kwargs):
        thread.start_new_thread(func, (self, ) + args, kwargs)

    return dec


class Mixin(object):

    def __init__(self, *args):
        self.lock = threading.Lock()

    def notify(self, subject, body, retries=5):
        pass


class NaiveMixin(Mixin):

    def __init__(self, conf):

        super(NaiveMixin, self).__init__()

        try:
             print(" * connecting to SMTP server", end=" ")
             mailer = notify.SMTPMailer(conf)
             print("[%s]" % colors.green("ok"))
        except (socket.error, smtplib.SMTPException):
             print("[%s]" % colors.red("failed"))
             mailer = notify.NullMailer()

        self.mailer = mailer

        if not conf.get("general", "host").startswith(("http://", "https://")):
            raise SystemExit("error: host must start with http:// or https://")

        try:
             print(" * connecting to HTTP server", end=" ")
             rv = urlparse.urlparse(conf.get("general", "host"))
             host = (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc
             httplib.HTTPConnection(host, timeout=5).request('GET', rv.path)
             print("[%s]" % colors.green("ok"))
        except (httplib.HTTPException, socket.error):
             print("[%s]" % colors.red("failed"))

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
                    time.sleep(0.01)

                uwsgi.queue_set(0, "LOCK")

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
