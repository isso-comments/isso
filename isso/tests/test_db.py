
try:
    import unittest2 as unittest
except ImportError:
    import unittest

import os
import sqlite3
import tempfile

from isso.db import SQLite3
from isso.core import Config


class TestDBMigration(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def test_defaults(self):

        db = SQLite3(self.path, Config.load(None))

        self.assertEqual(db.version, SQLite3.MAX_VERSION)
        self.assertTrue(db.preferences.get("session-key", "").isalnum())

    def test_session_key_migration(self):

        conf = Config.load(None)
        conf.set("general", "session-key", "supersecretkey")

        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version = 1")
            con.execute("CREATE TABLE threads (id INTEGER PRIMARY KEY)")

        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)
        self.assertEqual(db.preferences.get("session-key"),
                         conf.get("general", "session-key"))

        # try again, now with the session-key removed from our conf
        conf.remove_option("general", "session-key")
        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)
        self.assertEqual(db.preferences.get("session-key"),
                         "supersecretkey")
