# -*- encoding: utf-8 -*-

import time
import logging
import threading
import multiprocessing

try:
    import uwsgi
except ImportError:
    uwsgi = None

import _thread as thread

from isso.utils.cache import NullCache
from isso.utils.cache import SimpleCache

logger = logging.getLogger("isso")

# With email verification on, unverified comments expire long before the
# default `purge-after`, so the purge job must run at least this often.
UNVERIFIED_PURGE_INTERVAL = 3600


def purge_schedule(conf):
    """
    Return ``(max_age, interval)`` for the purge job: pending comments older
    than ``max_age`` seconds are deleted every ``interval`` seconds.
    """
    max_age = conf.getint("moderation", "purge-after")
    if conf.getboolean("general", "require-email-verification"):
        return max_age, min(max_age, UNVERIFIED_PURGE_INTERVAL)
    return max_age, max_age


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
        thread.start_new_thread(func, (self,) + args, kwargs)

    return dec


class ThreadedMixin(Mixin):
    def __init__(self, conf):
        super(ThreadedMixin, self).__init__(conf)

        if conf.getboolean("moderation", "enabled") or conf.getboolean("general", "require-email-verification"):
            self.purge(*purge_schedule(conf))

        self.cache = Cache(SimpleCache(threshold=1024, default_timeout=3600))

    @threaded
    def purge(self, max_age, interval):
        while True:
            with self.lock:
                self.db.comments.purge(max_age)
            time.sleep(interval)


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

        max_age, interval = purge_schedule(conf)

        def purge(signum):
            return self.db.comments.purge(max_age)

        uwsgi.register_signal(1, "", purge)
        uwsgi.add_timer(1, interval)

        # run purge once
        purge(1)
