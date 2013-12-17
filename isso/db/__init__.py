# -*- encoding: utf-8 -*-

import sqlite3
import logging

logger = logging.getLogger("isso")

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard


class SQLite3:

    MAX_VERSION = 1

    def __init__(self, path, conf):

        self.path = path
        self.conf = conf

        rv = self.execute([
            "SELECT name FROM sqlite_master"
            "   WHERE type='table' AND name IN ('threads', 'comments')"]
        ).fetchall()

        if rv:
            self.migrate(to=SQLite3.MAX_VERSION)
        else:
            self.execute("PRAGMA user_version = %i" % SQLite3.MAX_VERSION)

        self.threads = Threads(self)
        self.comments = Comments(self)
        self.guard = Guard(self)

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

        logger.info("migrate database from version %i to %i", self.version, to)

        if self.version == 0:

            from isso.utils import Bloomfilter
            bf = buffer(Bloomfilter(iterable=["127.0.0.0"]).array)

            with sqlite3.connect(self.path) as con:
                con.execute('UPDATE comments SET voters=?', (bf, ))
                con.execute('PRAGMA user_version = 1')
                logger.info("%i rows changed", con.total_changes)
