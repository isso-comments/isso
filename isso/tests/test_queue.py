# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import datetime

from isso.queue import Message, Queue, Full, Empty, Timeout


class TestMessage(unittest.TestCase):

    def test_message(self):
        a = Message("Foo", None)
        b = Message("Bar", None)

        self.assertLess(a, b)

    def test_message_delay(self):
        a = Message("Foo", None, delay=1)
        b = Message("Bar", None, delay=0)

        self.assertGreater(a, b)

    def test_message_wait(self):
        a = Message("Foo", None)
        b = Message("Foo", None)
        a = Queue.delay(a, 1, delayfunc=lambda i: 0.5)

        self.assertGreater(a, b)


class TestQueue(unittest.TestCase):

    def test_queue(self):
        q = Queue()
        msgs = [Message("Foo", None) for _ in range(3)]

        for msg in msgs:
            q.put(msg)

        self.assertEqual(q.size, 3)

        for msg in msgs:
            self.assertEqual(q.get(), msg)

        self.assertEqual(q.size, 0)


    def test_queue_full(self):
        q = Queue(maxlen=1)
        q.put(Message("Foo", None))

        self.assertRaises(Full, q.put, Message("Bar", None))

    def test_queue_empty(self):
        q = Queue()
        msg = Message("Foo", None)

        self.assertRaises(Empty, q.get)
        q.put(msg)
        q.get()
        self.assertRaises(Empty, q.get)

    def test_retry(self):
        q = Queue()
        msg = Message("Foo", None)

        q.retry(msg)
        self.assertRaises(Empty, q.get)
        self.assertEqual(q.size, 1)

    def test_retry_timeout(self):
        q = Queue(timeout=0)
        msg = Message("Foo", None)

        self.assertRaises(Timeout, q.retry, msg)

    def test_requeue(self):
        q = Queue()
        msg = Message("Foo", None)

        q.put(msg)
        q.requeue(q.get(), datetime.timedelta(seconds=1))

        self.assertRaises(Empty, q.get)
        self.assertEqual(q.size, 1)
