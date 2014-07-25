# -*- encoding: utf-8 -*-

from __future__ import unicode_literals, division

import json
import logging
import threading

import math
import bisect
import functools

import time

try:
    import queue
except ImportError:
    import Queue as queue

from isso.tasks import Cron
from isso.compat import iteritems

logger = logging.getLogger("isso")

Full = queue.Full
Empty = queue.Empty


class Retry(Exception):
    pass


class Timeout(Exception):
    pass


@functools.total_ordering
class Message(object):
    """Queue payload sortable by time.

    :param type: task type
    :param data: task payload
    :param delay: initial delay before the job gets executed
    :param wait: subsequent delays for retrying
    """

    def __init__(self, type, data, delay=0, wait=0):
        self.type = type
        self.data = data

        self.wait = wait
        self.timestamp = time.time() + delay

    def __le__(self, other):
        return self.timestamp + self.wait <= other.timestamp + other.wait

    def __eq__(self, other):
        return self.type == other.type and self.data == other.data

    def __repr__(self):
        return "<Message {0}: {1}>".format(self.type, self.data)


class Queue(object):
    """An in-memory queue with requeuing abilities.

    :param maxlen: upperbound limit
    :param timeout: maximum retry interval after which a :func:`retry` call
                    raises :exception:`Timeout` (defaults to ~34 min)
    """

    def __init__(self, maxlen=-1, timeout=2**10):
        self.queue = []
        self.maxlen = maxlen
        self.timeout = timeout

        # lock destructive queue operations
        self.mutex = threading.Lock()

    def put(self, item):
        with self.mutex:
            if -1 < self.maxlen < len(self.queue) + 1:
                raise queue.Full

            bisect.insort(self.queue, item)

    def get(self):
        with self.mutex:
            try:
                msg = self.queue.pop(0)
            except IndexError:
                raise queue.Empty

            if msg.timestamp + msg.wait <= time.time():
                return msg

            self.queue.insert(0, msg)

        raise queue.Empty

    def retry(self, msg):
        self.put(Queue.delay(msg, self.timeout))

    def requeue(self, msg, timedelta):
        self.put(Message(msg.type, msg.data, timedelta.total_seconds()))

    @property
    def size(self):
        with self.mutex:
            return len(self.queue)

    @classmethod
    def delay(cls, msg, timeout, delayfunc=lambda i: max(1, i * 2)):
        wait = delayfunc(msg.wait)
        if wait >= timeout:
            raise Timeout("Exceeded time limit of {0}".format(timeout))
        return Message(msg.type, msg.data, 0, wait)


class Worker(threading.Thread):
    """Thread that pulls data from the queue, does the actual work. If the queue
    is empty, sleep for longer intervals (see :func:`wait` for details)

    On startup, all recurring tasks are automatically queued with zero delay
    to run at least once.

    A task may throw :exception Retry: to indicate a expected failure (e.g.
    network not reachable) and asking to retry later.

    :param queue: a Queue
    :param targets: a mapping of task names and the actual task objects"""

    interval = 0.05

    def __init__(self, queue, targets):
        super(Worker, self).__init__()

        self.alive = True
        self.queue = queue
        self.targets = targets

        for name, target in iteritems(targets):
            if isinstance(target, Cron):
                queue.put(Message(name, None))

    def run(self):
        while self.alive:
            try:
                payload = self.queue.get()
            except queue.Empty:
                Worker.wait(0.5)
            else:
                task = self.targets.get(payload.type)
                if task is None:
                    logger.warn("No such task '%s'", payload.type)
                    continue
                try:
                    logger.debug("Executing {0} with '{1}'".format(
                        payload.type, json.dumps(payload.data)))
                    task.run(payload.data)
                except Retry:
                    try:
                        self.queue.retry(payload)
                    except Timeout:
                        logger.exception("Uncaught exception while retrying "
                                         "%s.run", task)
                except Exception:
                    logger.exception("Uncaught exception while executing "
                                     "%s.run", task)
                finally:
                    if isinstance(task, Cron):
                        self.queue.requeue(payload, task.timedelta)

    def join(self, timeout=None):
        self.alive = False
        super(Worker, self).join(timeout)

    @classmethod
    def wait(cls, seconds):
        """Sleep for :param seconds: but split into :var interval: sleeps to
        be interruptable.
        """
        f, i = math.modf(seconds / Worker.interval)

        for x in range(int(i)):
            time.sleep(Worker.interval)

        time.sleep(f * Worker.interval)


from .sa import SAQueue

__all__ = ["Full", "Empty", "Retry", "Timeout", "Message", "Queue", "SAQueue"]
