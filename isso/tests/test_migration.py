# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest
import tempfile
from os.path import join, dirname

from isso import config

from isso.db import SQLite3
from isso.migrate import Disqus, WordPress, autodetect, Generic

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

        self.assertEqual(
            len(db.execute("SELECT id FROM comments").fetchall()), 2)

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

        self.assertEqual(
            len(db.execute("SELECT id FROM threads").fetchall()), 2)
        self.assertEqual(
            len(db.execute("SELECT id FROM comments").fetchall()), 7)

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

    def test_generic(self):
        filepath = join(dirname(__file__), "generic.json")
        tempf = tempfile.NamedTemporaryFile()

        db = SQLite3(tempf.name, conf)
        Generic(db, filepath).migrate()

        self.assertEqual(db.threads["/posts/0001/"]["title"], "Test+post")
        self.assertEqual(db.threads["/posts/0001/"]["id"], 1)

        self.assertEqual(db.threads["/posts/0007/"]["title"], "Nat+%26+Miguel")
        self.assertEqual(db.threads["/posts/0007/"]["id"], 2)

        self.assertEqual(
            len(db.execute("SELECT id FROM threads").fetchall()), 2)
        self.assertEqual(
            len(db.execute("SELECT id FROM comments").fetchall()), 2)

        comment = db.comments.get(1)
        self.assertEqual(comment["author"], "texas holdem")
        self.assertEqual(comment["text"], "Great men can't be ruled. by free online poker")
        self.assertEqual(comment["email"], "")
        self.assertEqual(comment["website"], "http://www.tigerspice.com")
        self.assertEqual(comment["remote_addr"], "0.0.0.0")

        comment = db.comments.get(2)
        self.assertEqual(comment["author"], "Richard Crinshaw")
        self.assertEqual(comment["text"], "Ja-make-a me crazzy mon :)\n")
        self.assertEqual(comment["email"], "105421439@87750645.com")
        self.assertEqual(comment["website"], "")
        self.assertEqual(comment["remote_addr"], "0.0.0.0")

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

        jf = '[{"comments": [{"email": "", "remote_addr": "0.0.0.0", '
        self.assertEqual(autodetect(jf), Generic)
