# -*- encoding: utf-8 -*-

import unittest
import os
import sqlite3
import tempfile

from isso import config
from isso.db import SQLite3


class TestDBMigration(unittest.TestCase):

    def setUp(self):
        fd, self.path = tempfile.mkstemp()

    def tearDown(self):
        os.unlink(self.path)

    def test_defaults(self):

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)
        self.assertTrue(db.preferences.get("session-key", "").isalnum())

    def test_session_key_migration(self):

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
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

    def test_limit_nested_comments(self):
        """Transform previously A -> B -> C comment nesting to A -> B, A -> C"""

        tree = {
            1: None,
            2: None,
            3: 2,
            4: 3,
            7: 3,
            5: 2,
            6: None
        }

        with sqlite3.connect(self.path) as con:
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
                        "    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB NOT NULL)")

            con.execute(
                "INSERT INTO threads (uri, title) VALUES (?, ?)", ("/", "Test"))
            for (id, parent) in tree.items():
                con.execute("INSERT INTO comments ("
                            "   id, parent, created, voters)"
                            "VALUEs (?, ?, ?, ?)", (id, parent, id, sqlite3.Binary(b"")))

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })
        SQLite3(self.path, conf)

        flattened = list({
            1: None,
            2: None,
            3: 2,
            4: 2,
            5: 2,
            6: None,
            7: 2
        }.items())

        with sqlite3.connect(self.path) as con:
            rv = con.execute(
                "SELECT id, parent FROM comments ORDER BY created").fetchall()
            self.assertEqual(flattened, rv)

    def test_comment_add_notification_column_migration(self):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version = 3")

            con.execute("CREATE TABLE comments ("
                        "    tid REFERENCES threads(id),"
                        "    id INTEGER PRIMARY KEY,"
                        "    parent INTEGER,"
                        "    created FLOAT NOT NULL, modified FLOAT,"
                        "    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB NOT NULL)")

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })

        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)

        with sqlite3.connect(self.path) as con:
            # assert that the "notification" column has been added
            rv = con.execute("SELECT name FROM pragma_table_info('comments') WHERE name='notification'").fetchone()
            self.assertEqual(rv, ("notification",))

    def test_comment_add_notification_column_migration_with_existing_column(self):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version = 3")

            con.execute("CREATE TABLE comments ("
                        "    tid REFERENCES threads(id),"
                        "    id INTEGER PRIMARY KEY,"
                        "    parent INTEGER,"
                        "    created FLOAT NOT NULL, modified FLOAT,"
                        "    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB NOT NULL,"
                        "    notification INTEGER DEFAULT 0)")

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })

        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)

    def test_comment_text_not_null_migration(self):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version = 4")

            con.execute("CREATE TABLE threads ("
                        "    id INTEGER PRIMARY KEY,"
                        "    uri VARCHAR UNIQUE,"
                        "    title VARCHAR)")
            con.execute("CREATE TABLE comments ("
                        "    tid REFERENCES threads(id),"
                        "    id INTEGER PRIMARY KEY,"
                        "    parent INTEGER,"
                        "    created FLOAT NOT NULL, modified FLOAT,"
                        "    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB NOT NULL,"
                        "    notification INTEGER DEFAULT 0)")

            con.execute(
                "INSERT INTO threads (uri, title) VALUES (?, ?)", ("/", "Test"))

            con.execute("INSERT INTO comments (id, parent, created, text, voters) VALUES (?, ?, ?, ?, ?)",
                        (1, None, 1, None, sqlite3.Binary(b"")))

            con.execute("INSERT INTO comments (id, parent, created, text, voters) VALUES (?, ?, ?, ?, ?)",
                        (2, 1, 2, "foo", sqlite3.Binary(b"")))

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })

        db = SQLite3(self.path, conf)

        self.assertEqual(db.version, SQLite3.MAX_VERSION)

        with sqlite3.connect(self.path) as con:
            # assert that the "text" field has "NOT NULL" constraint
            rv = con.execute("SELECT \"notnull\" FROM pragma_table_info('comments') WHERE name='text'").fetchone()
            self.assertEqual(rv, (1,))

            rv = con.execute("SELECT text FROM comments WHERE id IN (1, 2)").fetchall()
            self.assertEqual(rv, [("",), ("foo",)])

    def test_comment_text_not_null_migration_with_rollback_after_error(self):
        with sqlite3.connect(self.path) as con:
            con.execute("PRAGMA user_version = 4")

            con.execute("CREATE TABLE threads ("
                        "    id INTEGER PRIMARY KEY,"
                        "    uri VARCHAR UNIQUE,"
                        "    title VARCHAR)")

            # emulate a migration error by creating a source table without the "notification" field
            con.execute("CREATE TABLE comments ("
                        "    tid REFERENCES threads(id),"
                        "    id INTEGER PRIMARY KEY,"
                        "    parent INTEGER,"
                        "    created FLOAT NOT NULL, modified FLOAT,"
                        "    text VARCHAR, author VARCHAR, email VARCHAR, website VARCHAR,"
                        "    mode INTEGER,"
                        "    remote_addr VARCHAR,"
                        "    likes INTEGER DEFAULT 0,"
                        "    dislikes INTEGER DEFAULT 0,"
                        "    voters BLOB NOT NULL)")

            con.execute(
                "INSERT INTO threads (uri, title) VALUES (?, ?)", ("/", "Test"))

            con.execute("INSERT INTO comments (id, parent, created, text, voters) VALUES (?, ?, ?, ?, ?)",
                        (1, None, 1, None, sqlite3.Binary(b"")))

            con.execute("INSERT INTO comments (id, parent, created, text, voters) VALUES (?, ?, ?, ?, ?)",
                        (2, 1, 2, "foo", sqlite3.Binary(b"")))

        conf = config.new({
            "general": {
                "dbpath": "/dev/null",
                "max-age": "1h"
            }
        })

        try:
            SQLite3(self.path, conf)
        except RuntimeError as e:
            self.assertEqual(str(e), "Migrating DB version 4 to 5 failed: no such column: notification")

        with sqlite3.connect(self.path) as con:
            # assert that DB version has not been updated
            rv = con.execute("PRAGMA user_version").fetchone()
            self.assertEqual(rv, (4,))

            # assert that the "text" field has no "NOT NULL" constraint
            rv = con.execute("SELECT \"notnull\" FROM pragma_table_info('comments') WHERE name='text'").fetchone()
            self.assertEqual(rv, (0,))

            rv = con.execute("SELECT text FROM comments WHERE id IN (1, 2)").fetchall()
            self.assertEqual(rv, [(None,), ("foo",)])
