# -*- encoding: utf-8 -*-

from __future__ import print_function

import io
import time
import logging
import threading
import multiprocessing

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

from isso.utils import parse
from isso.compat import text_type as str

from werkzeug.contrib.cache import NullCache, SimpleCache

logger = logging.getLogger("isso")


class Section:

    def __init__(self, conf, section):
        self.conf = conf
        self.section = section

    def get(self, key):
        return self.conf.get(self.section, key)

    def getint(self, key):
        return self.conf.getint(self.section, key)

    def getlist(self, key):
        return self.conf.getlist(self.section, key)

    def getiter(self, key):
        return self.conf.getiter(self.section, key)

    def getboolean(self, key):
        return self.conf.getboolean(self.section, key)


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
    ... spam = a, b, cdef
    ... bla =
    ...     spam
    ...     ham
    ... asd = fgh
    ... '''))
    >>> parser.getint("foo", "bar")
    3600
    >>> parser.getint("foo", "baz")
    12
    >>> parser.getlist("foo", "spam")  # doctest: +IGNORE_UNICODE
    ['a', 'b', 'cdef']
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

    def getlist(self, section, key):
        return list(map(str.strip, self.get(section, key).split(',')))

    def getiter(self, section, key):
        for item in map(str.strip, self.get(section, key).split('\n')):
            if item:
                yield item

    def section(self, section):
        return Section(self, section)


class Config:

    default = [
        "[general]",
        "name = ",
        "dbpath = /tmp/isso.db",
        "host = http://localhost:8080/", "max-age = 15m",
        "notify = ",
        "[moderation]",
        "enabled = false",
        "purge-after = 30d",
        "[server]",
        "listen = http://localhost:8080/",
        "reload = off", "profile = off",
        "[smtp]",
        "username = ", "password = ",
        "host = localhost", "port = 587", "security = starttls",
        "to = ", "from = ",
        "timeout = 10",
        "[guard]",
        "enabled = true",
        "ratelimit = 2",
        "direct-reply = 3",
        "reply-to-self = false",
        "[markup]",
        "options = strikethrough, superscript, autolink",
        "allowed-elements = ",
        "allowed-attributes = "
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
                if item in (("server", "host"), ("server", "port")):
                    logger.warn("use `listen = http://$host:$port` instead")
                if item == ("smtp", "ssl"):
                    logger.warn("use `security = none | starttls | ssl` instead")
                if item == ("general", "session-key"):
                    logger.info("Your `session-key` has been stored in the "
                                "database itself, this option is now unused")

        if rv.get("smtp", "username") and not rv.get("general", "notify"):
            logger.warn(("SMTP is no longer enabled by default, add "
                         "`notify = smtp` to the general section to "
                         "enable SMTP nofications."))

        return rv


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

        self.cache = Cache(SimpleCache(threshold=1024, default_timeout=3600))

    @threaded
    def purge(self, delta):
        while True:
            with self.lock:
                self.db.comments.purge(delta)
            time.sleep(delta)


class ProcessMixin(ThreadedMixin):

    def __init__(self, conf):

        super(ProcessMixin, self).__init__(conf)
        self.lock = multiprocessing.Lock()


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

        self.lock = multiprocessing.Lock()
        self.cache = uWSGICache

        timedelta = conf.getint("moderation", "purge-after")
        purge = lambda signum: self.db.comments.purge(timedelta)
        uwsgi.register_signal(1, "", purge)
        uwsgi.add_timer(1, timedelta)

        # run purge once
        purge(1)
