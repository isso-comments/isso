# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import unittest

from isso import config
from isso.db import SQLite3, Adapter

from isso.compat import iteritems


class TestSQLite3(unittest.TestCase):

    def test_connection(self):
        con = SQLite3(":memory:")

        con.connect()
        self.assertTrue(hasattr(con.local, "conn"))

        con.close()
        self.assertIsNone(con.local.conn)

    def test_autoconnect(self):
        con = SQLite3(":memory:")
        con.execute("")
        self.assertTrue(hasattr(con.local, "conn"))

    def test_rollback(self):
        con = SQLite3(":memory:")
        con.execute("CREATE TABLE foo (bar INTEGER)")
        con.execute("INSERT INTO foo (bar) VALUES (42)")

        try:
            with con.transaction as con:
                con.execute("INSERT INTO foo (bar) VALUES (23)")
                raise ValueError("some error")
        except ValueError:
            pass

        self.assertEqual(len(con.execute("SELECT bar FROM foo").fetchall()), 1)


class TestDBMigration(unittest.TestCase):

    def test_defaults(self):

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
        db = Adapter(SQLite3(":memory:"), conf)

        self.assertEqual(db.version, Adapter.MAX_VERSION)
        self.assertTrue(db.preferences.get("session-key", "").isalnum())

    def test_session_key_migration(self):

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
        conf.set("general", "session-key", "supersecretkey")

        connection = SQLite3(":memory:")

        with connection.transaction as con:
            con.execute("PRAGMA user_version = 1")
            con.execute("CREATE TABLE threads (id INTEGER PRIMARY KEY)")

        db = Adapter(connection, conf)

        self.assertEqual(db.version, Adapter.MAX_VERSION)
        self.assertEqual(db.preferences.get("session-key"),
                         conf.get("general", "session-key"))

        # try again, now with the session-key removed from our conf
        conf.remove_option("general", "session-key")
        db = Adapter(connection, conf)

        self.assertEqual(db.version, Adapter.MAX_VERSION)
        self.assertEqual(db.preferences.get("session-key"),
                         "supersecretkey")

    def test_limit_nested_comments(self):

        tree = {
            1: None,
            2: None,
               3: 2,
                  4: 3,
                  7: 3,
               5: 2,
            6: None
        }

        connection = SQLite3(":memory:")

        with connection.transaction as con:
            con.execute("PRAGMA user_version = 2")
            con.execute("CREATE TABLE threads ("
                        "    id INTEGER PRIMARY KEY,"
                        "    uri VARCHAR UNIQUE,"
                        "    title VARCHAR)")
            con.execute("CREATE TABLE comments ("
                        "    tid REFERENCES threads(id),"
                        "    id INTEGER PRIMARY KEY,"
                        "    parent INTEGER,"
                        "    created FLOAT NOT NULL, modified FLOAT,"
                        "    text VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB)")

            con.execute("INSERT INTO threads (uri, title) VALUES (?, ?)", ("/", "Test"))
            for (id, parent) in iteritems(tree):
                con.execute("INSERT INTO comments ("
                            "   tid, parent, created)"
                            "VALUEs (?, ?, ?)", (id, parent, id))

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
        Adapter(connection, conf)

        flattened = [
            (1, None),
            (2, None),
            (3, 2),
            (4, 2),
            (5, 2),
            (6, None),
            (7, 2)
        ]

        with connection.transaction as con:
            rv = con.execute("SELECT id, parent FROM comments ORDER BY created").fetchall()
            self.assertEqual(flattened, rv)
