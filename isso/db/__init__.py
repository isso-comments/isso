# -*- encoding: utf-8 -*-

import logging

logger = logging.getLogger("isso")

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard

from sqlalchemy import MetaData, create_engine


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

        logger.debug(uri)

        self.engine = create_engine(uri, echo=True)
        self.conf = conf

        # Get table definitions from all modules
        self.metadata = MetaData()

        self.threads = Threads(self, self.metadata)
        self.comments = Comments(self, self.metadata)
        self.guard = Guard(self)

        # Metadata is now filled with table definitions form Threads and Comments
        self.metadata.create_all(self.engine)

        # TODO: Does not work in PG and MY
        # self.execute("""
        #     CREATE TRIGGER IF NOT EXISTS remove_stale_threads
        #     AFTER DELETE ON comments
        #     BEGIN
        #         DELETE FROM threads WHERE id NOT IN (SELECT tid FROM comments);
        #     END
        #     """)

    def drop(self):
        self.metadata.drop_all(self.engine)

    def execute(self, statement, *multiparams, **params):
        """
        Execute given SQL. If given SQL is a list or tuple it will be concatenated.
        """

        if isinstance(statement, (list, tuple)):
            statement = ' '.join(statement)

        return self.engine.execute(statement, *multiparams, **params)

    def version(self):
        if self.engine.driver == 'pysqlite':
            return self.execute('PRAGMA user_version').fetchone()[0]
        else:
            return self.execute('SELECT version FROM schema_version').fetchone()[0]
