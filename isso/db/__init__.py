# -*- encoding: utf-8 -*-

import sqlite3
import logging
import operator
import os.path

from collections import defaultdict

logger = logging.getLogger("isso")

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard
from isso.db.preferences import Preferences


class SQLite3:
    """DB-dependend wrapper around SQLite3.

    Runs migration if `user_version` is older than `MAX_VERSION` and register
    a trigger for automated orphan removal.
    """

    MAX_VERSION = 5

    def __init__(self, path, conf):

        self.path = os.path.expanduser(path)
        self.conf = conf

        rv = self.execute([
            "SELECT name FROM sqlite_master"
            "   WHERE type='table' AND name IN ('threads', 'comments', 'preferences')"]
        ).fetchone()

        self.preferences = Preferences(self)
        self.threads = Threads(self)
        self.comments = Comments(self)
        self.guard = Guard(self)

        if rv is None:
            self.execute("PRAGMA user_version = %i" % SQLite3.MAX_VERSION)
        else:
            self.migrate(to=SQLite3.MAX_VERSION)

        self.execute([
            'CREATE TRIGGER IF NOT EXISTS remove_stale_threads',
            'AFTER DELETE ON comments',
            'BEGIN',
            '    DELETE FROM threads WHERE id NOT IN (SELECT tid FROM comments);',
            'END'])

    def execute(self, sql, args=()):

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        with sqlite3.connect(self.path) as con:
            return con.execute(sql, args)

    @property
    def version(self):
        return self.execute("PRAGMA user_version").fetchone()[0]

    def migrate(self, to):

        if self.version >= to:
            return

        logger.info("Migrating database from version %i to %i", self.version, to)

        # re-initialize voters blob due a bug in the bloomfilter signature
        # which added older commenter's ip addresses to the current voters blob
        if self.version == 0:

            from isso.utils import Bloomfilter
            bf = memoryview(Bloomfilter(iterable=["127.0.0.0"]).array)

            with sqlite3.connect(self.path) as con:
                con.execute("BEGIN TRANSACTION")
                try:
                    con.execute('UPDATE comments SET voters=?', (bf, ))
                    con.execute('PRAGMA user_version = 1')
                    con.execute("COMMIT")
                    logger.info("Migrating DB version 0 to 1 by re-initializing voters blob, %i rows changed",
                                con.total_changes)
                except sqlite3.Error as e:
                    con.execute("ROLLBACK")
                    logger.error("Migrating DB version 0 to 1 failed: %s", e)
                    raise RuntimeError("Migrating DB version 0 to 1 failed: %s" % e)

        # move [general] session-key to database
        if self.version == 1:

            with sqlite3.connect(self.path) as con:
                con.execute("BEGIN TRANSACTION")
                try:
                    if self.conf.has_option("general", "session-key"):
                        con.execute('UPDATE preferences SET value=? WHERE key=?', (
                            self.conf.get("general", "session-key"), "session-key"))

                    con.execute('PRAGMA user_version = 2')
                    con.execute("COMMIT")
                    logger.info("Migrating DB version 1 to 2 by moving session-key to database, %i rows changed",
                                con.total_changes)
                except sqlite3.Error as e:
                    con.execute("ROLLBACK")
                    logger.error("Migrating DB version 1 to 2 failed: %s", e)
                    raise RuntimeError("Migrating DB version 1 to 2 failed: %s" % e)

        # limit max. nesting level to 1
        if self.version == 2:

            def first(rv):
                return list(map(operator.itemgetter(0), rv))

            with sqlite3.connect(self.path) as con:
                top = first(con.execute(
                    "SELECT id FROM comments WHERE parent IS NULL").fetchall())
                flattened = defaultdict(set)

                for id in top:

                    ids = [id, ]

                    while ids:
                        rv = first(con.execute(
                            "SELECT id FROM comments WHERE parent=?", (ids.pop(), )))
                        ids.extend(rv)
                        flattened[id].update(set(rv))

                con.execute("BEGIN TRANSACTION")
                try:
                    for id in flattened.keys():
                        for n in flattened[id]:
                            con.execute(
                                "UPDATE comments SET parent=? WHERE id=?", (id, n))

                    con.execute('PRAGMA user_version = 3')
                    con.execute("COMMIT")
                    logger.info("Migrating DB version 2 to 3 by limiting nesting level to 1, %i rows changed",
                                con.total_changes)
                except sqlite3.Error as e:
                    con.execute("ROLLBACK")
                    logger.error("Migrating DB version 2 to 3 failed: %s", e)
                    raise RuntimeError("Migrating DB version 2 to 3 failed: %s" % e)

        # add notification field to comments (moved from Comments class to migration)
        if self.version == 3:
            with sqlite3.connect(self.path) as con:
                self.migrate_to_version_4(con)

        # "text" field in "comments" became NOT NULL
        if self.version == 4:
            with sqlite3.connect(self.path) as con:
                con.execute("BEGIN TRANSACTION")
                con.execute("UPDATE comments SET text = '' WHERE text IS NULL")

                # create new table with NOT NULL constraint for "text" field
                con.execute(Comments.create_table_query("comments_new"))

                try:
                    # copy data from old table to new table
                    con.execute("""
                        INSERT INTO comments_new (
                            tid, id, parent, created, modified, mode, remote_addr, text, author, email, website, likes, dislikes, voters, notification
                        )
                        SELECT
                            tid, id, parent, created, modified, mode, remote_addr, text, author, email, website, likes, dislikes, voters, notification
                        FROM comments
                    """)

                    # swap tables and drop old table
                    con.execute("ALTER TABLE comments RENAME TO comments_backup_v4")
                    con.execute("ALTER TABLE comments_new RENAME TO comments")
                    con.execute("DROP TABLE comments_backup_v4")

                    con.execute('PRAGMA user_version = 5')
                    con.execute("COMMIT")
                    logger.info("Migrating DB version 4 to 5 by setting empty comments.text to '', %i rows changed",
                                con.total_changes)
                except sqlite3.Error as e:
                    con.execute("ROLLBACK")
                    logger.error("Migrating DB version 4 to 5 failed: %s", e)
                    raise RuntimeError("Migrating DB version 4 to 5 failed: %s" % e)

    def migrate_to_version_4(self, con):
        # check if "notification" column exists in "comments" table
        rv = con.execute("PRAGMA table_info(comments)").fetchall()
        if any([row[1] == 'notification' for row in rv]):
            logger.info("Migrating DB version 3 to 4 skipped, 'notification' field already exists in comments")
            con.execute('PRAGMA user_version = 4')
            return

        con.execute("BEGIN TRANSACTION")
        try:
            con.execute('ALTER TABLE comments ADD COLUMN notification INTEGER DEFAULT 0;')
            con.execute('PRAGMA user_version = 4')
            con.execute("COMMIT")
            logger.info("Migrating DB version 3 to 4 by adding 'notification' field to comments")
        except sqlite3.Error as e:
            con.execute("ROLLBACK")
            logger.error("Migrating DB version 3 to 4 failed: %s", e)
            raise RuntimeError("Migrating DB version 3 to 4 failed: %s" % e)
