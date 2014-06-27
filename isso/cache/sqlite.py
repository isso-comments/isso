# -*- encoding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from . import Base
from isso.db import SQLite3


class SQLite3Cache(Base):
    """Implements a shared cache using SQLite3. Works across multiple processes
    and threads, concurrent writes are not supported.

    JSON is used to serialize python primitives in a safe way.
    """

    serialize = True

    def __init__(self, connection, threshold=1024, timeout=-1):
        super(SQLite3Cache, self).__init__(threshold, timeout)
        self.connection = connection
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS cache ('
            '    key TEXT PRIMARY KEY,'
            '    value BLOB,'
            '    time FLOAT)')

        # drop trigger, in case threshold has changed
        self.connection.execute('DROP TRIGGER IF EXISTS sweeper')
        self.connection.execute([
            'CREATE TRIGGER sweeper AFTER INSERT ON cache',
            'BEGIN',
            '    DELETE FROM cache WHERE key NOT IN ('
            '        SELECT key FROM cache',
            '        ORDER BY time DESC LIMIT {0}'.format(threshold),
            '    );',
            'END'])

    def _get(self, ns, key, default=None):
        rv = self.connection.execute(
            'SELECT value FROM cache WHERE key = ?',
            (ns + b'-' + key, )).fetchone()

        if rv is None:
            raise KeyError

        return rv[0]

    def _set(self, ns, key, value):
        with self.connection.transaction as con:
            con.execute(
                'INSERT OR REPLACE INTO cache (key, value, time) VALUES (?, ?, ?)',
                (ns + b'-' + key, value, time.time()))

    def _delete(self, ns, key):
        with self.connection.transaction as con:
            con.execute('DELETE FROM cache WHERE key = ?', (ns + b'-' + key, ))
