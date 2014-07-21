# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso import db
from isso.controllers import comments, threads


class TestController(unittest.TestCase):

    def setUp(self):
        _db = db.Adapter("sqlite:///:memory:")
        self.comments = comments.Controller(_db)
        self.threads = threads.Controller(_db)

    def test_new(self):
        thread = self.threads.new("/", None)

        self.assertEqual(thread.id, 1)
        self.assertEqual(thread.uri, "/")
        self.assertEqual(thread.title, None)

    def test_get(self):
        self.assertIsNone(self.threads.get("/"))

        th = self.threads.get(self.threads.new("/", None).uri)
        self.assertIsNotNone(th)

        self.assertEqual(th.id, 1)
        self.assertEqual(th.uri, "/")
        self.assertEqual(th.title, None)

    def test_delete(self):
        th = self.threads.new("/", None)
        self.threads.delete(th.uri)

        self.assertIsNone(self.threads.get(th.uri))

    def test_delete_removes_comments(self):
        th = self.threads.new("/", None)
        cg = self.threads.new("/control/group", None)

        for _ in range(3):
            self.comments.new("127.0.0.1", th, dict(text="..."))
            self.comments.new("127.0.0.1", cg, dict(text="..."))

        self.assertEqual(self.comments.count(th), [3])
        self.assertEqual(self.comments.count(cg), [3])

        # now remove the thread
        self.threads.delete(th.uri)

        self.assertEqual(self.comments.count(th), [0])
        self.assertEqual(self.comments.count(cg), [3])
