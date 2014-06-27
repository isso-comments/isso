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

from isso.compat import PY2K

if PY2K:
    import thread
else:
    import _thread as thread

logger = logging.getLogger("isso")


class Mixin(object):

    def __init__(self, conf):
        self.lock = threading.Lock()

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


class uWSGIMixin(Mixin):

    def __init__(self, conf):

        super(uWSGIMixin, self).__init__(conf)

        self.lock = multiprocessing.Lock()

        timedelta = conf.getint("moderation", "purge-after")
        purge = lambda signum: self.db.comments.purge(timedelta)
        uwsgi.register_signal(1, "", purge)
        uwsgi.add_timer(1, timedelta)

        # run purge once
        purge(1)
