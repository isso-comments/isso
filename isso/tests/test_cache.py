# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso.compat import text_type as str

from isso.db import SQLite3
from isso.cache import Cache, SQLite3Cache

ns = "test"


class TestCache(unittest.TestCase):

    def setUp(self):
        self.cache = Cache(threshold=8)

    def test_cache(self):
        cache = self.cache

        cache.delete(ns, "foo")
        self.assertIsNone(cache.get(ns, "foo"))

        cache.set(ns, "foo", "bar")
        self.assertEqual(cache.get(ns, "foo"), "bar")

        cache.delete(ns, "foo")
        self.assertIsNone(cache.get(ns, "foo"))

    def test_full(self):
        cache = self.cache

        cache.set(ns, "foo", "bar")

        for i in range(7):
            cache.set(ns, str(i), "Spam!")

        for i in range(7):
            self.assertEqual(cache.get(ns, str(i)), "Spam!")

        self.assertIsNotNone(cache.get(ns, "foo"))

        cache.set(ns, "bar", "baz")
        self.assertIsNone(cache.get(ns, "foo"))

    def test_primitives(self):
        cache = self.cache

        for val in (None, True, [1, 2, 3], {"bar": "baz"}):
            cache.set(ns, "val", val)
            self.assertEqual(cache.get(ns, "val"), val, val.__class__.__name__)


class TestSQLite3Cache(TestCache):

    def setUp(self):
        self.cache = SQLite3Cache(SQLite3(":memory:"), threshold=8)
