# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import json
import time

from sqlalchemy import Table, Column, MetaData, create_engine
from sqlalchemy import Integer, Float, String, LargeBinary
from sqlalchemy.sql import select, func

from . import Queue, Full, Empty, Message


pickle = lambda val: json.dumps(val).encode("utf-8")
unpickle = lambda val: json.loads(val.decode("utf-8"))


class SAQueue(Queue):
    """Implements a shared queue using SQLAlchemy Core
    """

    def __init__(self, db, maxlen=-1, timeout=2**10):
        super(SAQueue, self).__init__(maxlen, timeout)
        self.metadata = MetaData()
        self.engine = create_engine(db)
        self.queue = Table("queue", self.metadata,
            Column("id", Integer, primary_key=True),
            Column("type", String(16)),
            Column("data", LargeBinary(65535)),
            Column("timestamp", Float),
            Column("wait", Float))

        self.metadata.create_all(self.engine)

    def put(self, item):
        with self.engine.begin() as con:
            count = self._size(con) + 1
            if -1 < self.maxlen < count:
                raise Full

            con.execute(self.queue.insert().values(
                type=item.type, data=pickle(item.data),
                timestamp=item.timestamp, wait=item.wait))

    def get(self):
        with self.engine.begin() as con:
            obj = con.execute(
                select([self.queue.c.id, self.queue.c.type, self.queue.c.data])
                .where(time.time() > self.queue.c.timestamp + self.queue.c.wait)
                .order_by(self.queue.c.timestamp)
                .limit(1)).fetchone()

            if not obj:
                raise Empty

            _id, _type, data = obj
            con.execute(self.queue.delete(self.queue.c.id == _id))

            return Message(_type, unpickle(data))

    def _size(self, con):
        return con.execute(select([func.count(self.queue)])).fetchone()[0]

    @property
    def size(self):
        return self._size(self.engine.connect())
