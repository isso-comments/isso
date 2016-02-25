# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import tempfile
from os.path import join, dirname

from isso import config

from isso.db import SQLite3
from isso.migrate import Disqus, WordPress, autodetect

conf = config.new({
    "general": {
        "dbpath": "/dev/null",
        "max-age": "1h"
    }
})


class TestMigration(unittest.TestCase):

    def test_disqus(self):

        xml = join(dirname(__file__), "disqus.xml")
        xxx = tempfile.NamedTemporaryFile()

        db = SQLite3(xxx.name, conf)
        Disqus(db, xml).migrate()

        self.assertEqual(len(db.execute("SELECT id FROM comments").fetchall()), 2)

        self.assertEqual(db.threads["/"]["title"], "Hello, World!")
        self.assertEqual(db.threads["/"]["id"], 1)

        a = db.comments.get(1)

        self.assertEqual(a["author"], "peter")
        self.assertEqual(a["email"], "foo@bar.com")
        self.assertEqual(a["remote_addr"], "127.0.0.0")

        b = db.comments.get(2)
        self.assertEqual(b["parent"], a["id"])

    def test_wordpress(self):

        xml = join(dirname(__file__), "wordpress.xml")
        xxx = tempfile.NamedTemporaryFile()

        db = SQLite3(xxx.name, conf)
        WordPress(db, xml).migrate()

        self.assertEqual(db.threads["/2014/test/"]["title"], "Hello, World…")
        self.assertEqual(db.threads["/2014/test/"]["id"], 1)

        self.assertEqual(db.threads["/?p=4"]["title"], "...")
        self.assertEqual(db.threads["/?p=4"]["id"], 2)

        self.assertEqual(len(db.execute("SELECT id FROM threads").fetchall()), 2)
        self.assertEqual(len(db.execute("SELECT id FROM comments").fetchall()), 7)

        first = db.comments.get(1)
        self.assertEqual(first["author"], "Ohai")
        self.assertEqual(first["text"], "Erster!1")
        self.assertEqual(first["remote_addr"], "82.119.20.0")

        second = db.comments.get(2)
        self.assertEqual(second["author"], "Tester")
        self.assertEqual(second["text"], "Zweiter.")

        for i in (3, 4, 5):
            self.assertEqual(db.comments.get(i)["parent"], second["id"])

        last = db.comments.get(6)
        self.assertEqual(last["author"], "Letzter :/")
        self.assertEqual(last["parent"], None)

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
