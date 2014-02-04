# -*- encoding: utf-8 -*-

import logging

logger = logging.getLogger("isso")

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard

from sqlalchemy import MetaData, create_engine, Table, Column, Integer, desc


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

        if self.engine.driver == 'pysqlite':
            self.sqlite = True
        else:
            self.sqlite = False

        # Get table definitions from all modules
        self.metadata = MetaData()

        if not self.sqlite:
            self.version_table = Table(
                'schema_version', self.metadata, Column('version', Integer))

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
        """
        Drop all tables. Reset database schema version.
        """

        self.metadata.drop_all(self.engine)

        if self.sqlite:
            self.execute('PRAGMA user_version = 0')

    def execute(self, statement, *multiparams, **params):
        """
        Execute given SQL. If given SQL is a list or tuple it will be concatenated.
        """

        if isinstance(statement, (list, tuple)):
            statement = ' '.join(statement)

        return self.engine.execute(statement, *multiparams, **params)

    @property
    def version(self):
        """
        Return current database schema version.

        On SQLite it will be read from user_version pragma, on other DBMS from the `schema_version`
        table.
        """
        if self.sqlite:
            return self.execute('PRAGMA user_version').fetchone()[0]
        else:
            return self.execute(self.version_table.select()).fetchone()[0]

    @version.setter
    def version(self, version):
        """
        Save new version integer to database.

        On SQLite it will be saved is user_version pragma. On other DBMS a table called
        `schema_version` will be used.
        """

        if self.sqlite:
            self.execute('PRAGMA user_version = ?', version)
        else:
            self.execute(self.version_table.delete())
            self.execute(self.version_table.insert().values(version=version))
