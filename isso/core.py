# -*- encoding: utf-8 -*-

from __future__ import print_function

import time
import logging
import threading
import multiprocessing

try:
    import uwsgi
except ImportError:
    uwsgi = None

import _thread as thread

from flask_caching.backends.nullcache import NullCache
from flask_caching.backends.simplecache import SimpleCache

logger = logging.getLogger("isso")


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

        def purge(signum):
            return self.db.comments.purge(timedelta)
        uwsgi.register_signal(1, "", purge)
        uwsgi.add_timer(1, timedelta)

        # run purge once
        purge(1)
