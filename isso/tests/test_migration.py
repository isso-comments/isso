# -*- encoding: utf-8 -*-

try:
    import unittest2 as unittest
except ImportError:
    import unittest

import tempfile
from os.path import join, dirname

from isso.core import Config

from isso.db import SQLite3
from isso.migrate import Disqus


class TestMigration(unittest.TestCase):

    def test_disqus(self):

        xml = join(dirname(__file__), "disqus.xml")
        xxx = tempfile.NamedTemporaryFile()

        db = SQLite3(xxx.name, Config.load(None))
        Disqus(db, xml).migrate()

        self.assertEqual(db.threads["/"]["title"], "Hello, World!")
        self.assertEqual(db.threads["/"]["id"], 1)

        a = db.comments.get(1)

        self.assertEqual(a["author"], "peter")
        self.assertEqual(a["email"], "foo@bar.com")

        b = db.comments.get(2)
        self.assertEqual(b["parent"] ,a["id"])


    a = db.comments.get(1)

    assert a["author"] == "peter"
    assert a["email"] == "foo@bar.com"

    b = db.comments.get(2)
    assert b["parent"] == a["id"]
