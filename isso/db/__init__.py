# -*- encoding: utf-8 -*-

import logging
import sqlalchemy

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

        The DB URI must be a string like `sqlite:////var/lib/isso/comments.db`
        that is understand by SQLAlchemy's `create_engine`.
        """

        self.engine = sqlalchemy.create_engine(uri)
        self.conf = conf

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
        """
        Execute given SQL. If given SQL is a list or tuple it will be concatenated.
        """

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        return self.engine.execute(sql, args)
