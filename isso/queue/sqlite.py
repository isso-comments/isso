# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import json
import time

from . import Queue, Full, Empty, Message


pickle = lambda val: json.dumps(val).encode("utf-8")
unpickle = lambda val: json.loads(val.decode("utf-8"))


class SQLite3Queue(Queue):
    """Implements a shared queue using SQLite3.

    :param connection: SQLite3 connection
    """

    def __init__(self, connection, maxlen=-1, timeout=2**10):
        super(SQLite3Queue, self).__init__(maxlen, timeout)
        self.connection = connection
        self.connection.execute(
            'CREATE TABLE IF NOT EXISTS queue ('
            '  id INTEGER PRIMARY KEY AUTOINCREMENT,'
            '  type TEXT,'
            '  data BLOB,'
            '  timestamp FLOAT,'
            '  wait FLOAT)')

    def put(self, item):
        with self.connection.transaction as con:
            count = con.execute('SELECT COUNT(*) FROM queue').fetchone()[0] + 1
            if -1 < self.maxlen < count:
                raise Full

            con.execute(
                'INSERT INTO queue (type, data, timestamp, wait) VALUES (?, ?, ?, ?)',
                (item.type, pickle(item.data), item.timestamp, item.wait))

    def get(self):
        with self.connection.transaction as con:
            row = con.execute(
                'SELECT id, type, data FROM queue '
                'WHERE (? > timestamp + wait) ORDER BY timestamp LIMIT 1',
                (time.time(), )).fetchone()
            if not row:
                raise Empty

            id, type, data = row
            con.execute('DELETE FROM queue WHERE id = ?', (str(id), ))
            return Message(type, unpickle(data))

    @property
    def size(self):
        with self.connection.transaction as con:
            return con.execute('SELECT COUNT(*) FROM queue').fetchone()[0]
