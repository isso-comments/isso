# -*- encoding: utf-8 -*-

from __future__ import print_function

import io
import os
import time
import binascii
import threading
import logging

import socket
import smtplib

from configparser import ConfigParser

try:
    import uwsgi
except ImportError:
    uwsgi = None

from isso.compat import PY2K

if PY2K:
    import thread
else:
    import _thread as thread

from isso import notify
from isso.utils import parse
from isso.compat import text_type as str

from werkzeug.contrib.cache import NullCache, SimpleCache

logger = logging.getLogger("isso")


class IssoParser(ConfigParser):
    """
    Extended :class:`ConfigParser` to parse human-readable timedeltas
    into seconds and handles multiple values per key.

    >>> import io
    >>> parser = IssoParser(allow_no_value=True)
    >>> parser.read_file(io.StringIO(u'''
    ... [foo]
    ... bar = 1h
    ... baz = 12
    ... bla =
    ...     spam
    ...     ham
    ... asd = fgh
    ... '''))
    >>> parser.getint("foo", "bar")
    3600
    >>> parser.getint("foo", "baz")
    12
    >>> list(parser.getiter("foo", "bla"))  # doctest: +IGNORE_UNICODE
    ['spam', 'ham']
    >>> list(parser.getiter("foo", "asd"))  # doctest: +IGNORE_UNICODE
    ['fgh']
    """

    @classmethod
    def _total_seconds(cls, td):
        return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6

    def getint(self, section, key):
        try:
            delta = parse.timedelta(self.get(section, key))
        except ValueError:
            return super(IssoParser, self).getint(section, key)
        else:
            try:
                return int(delta.total_seconds())
            except AttributeError:
                return int(IssoParser._total_seconds(delta))

    def getiter(self, section, key):
        for item in map(str.strip, self.get(section, key).split('\n')):
            if item:
                yield item


class Config:

    default = [
        "[general]",
        "dbpath = /tmp/isso.db", "session-key = %r" % binascii.b2a_hex(os.urandom(24)),
        "host = http://localhost:8080/", "max-age = 15m",
        "[moderation]",
        "enabled = false",
        "purge-after = 30d",
        "[server]",
        "host = localhost", "port = 8080", "reload = off",
        "[smtp]",
        "username = ", "password = ",
        "host = localhost", "port = 465", "ssl = on",
        "to = ", "from = ",
        "[guard]",
        "enabled = true",
        "ratelimit = 2"
        ""
    ]

    @classmethod
    def load(cls, configfile):

        # return set of (section, option)
        setify = lambda cp: set((section, option) for section in cp.sections()
                                for option in cp.options(section))

        rv = IssoParser(allow_no_value=True)
        rv.read_file(io.StringIO(u'\n'.join(Config.default)))

        a = setify(rv)

        if configfile:
            rv.read(configfile)

        diff = setify(rv).difference(a)

        if diff:
            for item in diff:
                logger.warn("no such option: [%s] %s", *item)

        return rv


def SMTP(conf):

    try:
        mailer = notify.SMTPMailer(conf)
        logger.info("connected to SMTP server")
    except (socket.error, smtplib.SMTPException):
        logger.warn("unable to connect to SMTP server")
        mailer = notify.NullMailer()

    return mailer


class Cache:
    """Wrapper around werkzeug's cache class, to make it compatible to
    uWSGI's cache framework.
    """

    def __init__(self, cache):
        self.cache = cache

    def get(self, cache, key):
        return self.cache.get(key)

    def set(self, cache, key, value):
        return self.cache.set(key, value)

    def delete(self, cache, key):
        return self.cache.delete(key)


class Mixin(object):

    def __init__(self, conf):
        self.lock = threading.Lock()
        self.cache = Cache(NullCache())

    def notify(self, subject, body, retries=5):
        pass


def threaded(func):
    """
    Decorator to execute each :param func: call in a separate thread.
    """

    def dec(self, *args, **kwargs):
        thread.start_new_thread(func, (self, ) + args, kwargs)

    return dec


class ThreadedMixin(Mixin):

    def __init__(self, conf):

        super(ThreadedMixin, self).__init__(conf)

        if conf.getboolean("moderation", "enabled"):
            self.purge(conf.getint("moderation", "purge-after"))

        self.mailer = SMTP(conf)
        self.cache = Cache(SimpleCache(threshold=1024, default_timeout=3600))

    @threaded
    def notify(self, subject, body, retries=5):

        for x in range(retries):
            try:
                self.mailer.sendmail(subject, body)
            except Exception:
                time.sleep(60)
            else:
                break

    @threaded
    def purge(self, delta):
        while True:
            with self.lock:
                self.db.comments.purge(delta)
            time.sleep(delta)


class uWSGICache(object):
    """Uses uWSGI Caching Framework. INI configuration:

    .. code-block:: ini

        cache2 = name=hash,items=1024,blocksize=32

    """

    @classmethod
    def get(self, cache, key):
        return uwsgi.cache_get(key, cache)

    @classmethod
    def set(self, cache, key, value):
        uwsgi.cache_set(key, value, 3600, cache)

    @classmethod
    def delete(self, cache, key):
        uwsgi.cache_del(key, cache)


class uWSGIMixin(Mixin):

    def __init__(self, conf):

        super(uWSGIMixin, self).__init__(conf)

        class Lock():

            def __enter__(self):
                uwsgi.lock()

            def __exit__(self, exc_type, exc_val, exc_tb):
                uwsgi.unlock()

        def spooler(args):
            try:
                self.mailer.sendmail(args["subject"].decode('utf-8'), args["body"].decode('utf-8'))
            except smtplib.SMTPConnectError:
                return uwsgi.SPOOL_RETRY
            else:
                return uwsgi.SPOOL_OK

        uwsgi.spooler = spooler

        self.lock = Lock()
        self.mailer = SMTP(conf)
        self.cache = uWSGICache

        timedelta = conf.getint("moderation", "purge-after")
        purge = lambda signum: self.db.comments.purge(timedelta)
        uwsgi.register_signal(1, "", purge)
        uwsgi.add_timer(1, timedelta)

        # run purge once
        purge(1)

    def notify(self, subject, body, retries=5):
        uwsgi.spool({"subject": subject.encode('utf-8'), "body": body.encode('utf-8')})
