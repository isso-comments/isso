# -*- encoding: utf-8 -*-

import logging
import sqlalchemy
import os.path
import pkgutil

logger = logging.getLogger("isso")

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard

class Adapter:
    """
    Database adapter using SQLAlchemy.
    """

    MAX_VERSION = 1

    def __init__(self, uri, conf):
        """
        Create new database adapter based on given DB-URI.

        The DB URI must be a string like `sqlite:///var/lib/isso/comments.db`
        that is understand by SQLAlchemy's `create_engine`.
        """

        self.engine = sqlalchemy.create_engine(uri)
        self.conf   = conf

        self.threads  = Threads(self)
        self.comments = Comments(self)
        self.guard    = Guard(self)

    def execute(self, sql, args=()):
        """
        Execute given SQL. If given SQL is a list or tuple it will be concatenated.
        """

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        with self.engine.connect() as con:
            return con.execute(sql, args)

class SQLite3Depricated:
    """DB-dependend wrapper around SQLite3.

    Runs migration if `user_version` is older than `MAX_VERSION` and register
    a trigger for automated orphan removal.
    """

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

        # re-initialize voters blob due a bug in the bloomfilter signature
        # which added older commenter's ip addresses to the current voters blob
        if self.version == 0:

            from isso.utils import Bloomfilter
            bf = buffer(Bloomfilter(iterable=["127.0.0.0"]).array)

            with sqlite3.connect(self.path) as con:
                con.execute('UPDATE comments SET voters=?', (bf, ))
                con.execute('PRAGMA user_version = 1')
                logger.info("%i rows changed", con.total_changes)
