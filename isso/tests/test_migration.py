# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
from os.path import join, dirname

from isso.db import Adapter
from isso.controllers import threads, comments
from isso.migrate import Disqus, WordPress, autodetect


class TestMigration(unittest.TestCase):

    def setUp(self):
        db = Adapter("sqlite:///:memory:")
        self.threads = threads.Controller(db)
        self.comments = comments.Controller(db)

    def test_disqus(self):

        Disqus(self.threads, self.comments).migrate(
            join(dirname(__file__), "disqus.xml"))

        th = self.threads.get("/")
        self.assertIsNotNone(th)
        self.assertEqual(th.title, "Hello, World!")
        self.assertEqual(th.id, 1)

        self.assertEqual(self.comments.count(th)[0], 2)

        a = self.comments.get(1)
        self.assertIsNotNone(a)

        self.assertEqual(a.author, "peter")
        self.assertEqual(a.email, "foo@bar.com")
        self.assertEqual(a.remote_addr, "127.0.0.0")

        b = self.comments.get(2)
        self.assertEqual(b.parent, a.id)

    def test_wordpress(self):
        WordPress(self.threads, self.comments).migrate(
            join(dirname(__file__), "wordpress.xml"))

        r = self.threads.get("/2014/test/")
        self.assertEqual(r.title, "Hello, World…")
        self.assertEqual(r.id, 1)

        s = self.threads.get("/?p=4")
        self.assertEqual(s.title, "...")
        self.assertEqual(s.id, 2)

        self.assertEqual(sum(self.comments.count(r, s)), 7)

        a = self.comments.get(1)
        self.assertEqual(a.author, "Ohai")
        self.assertEqual(a.text, "Erster!1")
        self.assertEqual(a.remote_addr, "82.119.20.0")

        b = self.comments.get(2)
        self.assertEqual(b.author, "Tester")
        self.assertEqual(b.text, "Zweiter.")

        for i in (3, 4, 5):
            self.assertEqual(self.comments.get(i).parent, b.id)

        last = self.comments.get(6)
        self.assertEqual(last.author, "Letzter :/")
        self.assertEqual(last.parent, None)

    def test_detection(self):

        wp = """\
                <?xml version="1.0" encoding="UTF-8"?>
                <rss version="2.0"
                    xmlns:content="http://purl.org/rss/1.0/modules/content/"
                    xmlns:dc="http://purl.org/dc/elements/1.1/"
                    xmlns:wp="http://wordpress.org/export/%s/">"""

        self.assertEqual(autodetect(wp % "foo"), None)

        for version in ("1.0", "1.1", "1.2", "1.3"):
            self.assertEqual(autodetect(wp % version), WordPress)

        dq = '''\
        <?xml version="1.0"?>
        <disqus xmlns="http://disqus.com"
                xmlns:dsq="http://disqus.com/disqus-internals"'''
        self.assertEqual(autodetect(dq), Disqus)
