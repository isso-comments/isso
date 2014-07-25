# -*- encoding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from sqlalchemy import Table, Column, MetaData, create_engine
from sqlalchemy import Float, String, LargeBinary
from sqlalchemy.sql import select, func

from . import Base


def get(con, cache, key):
    rv = con.execute(
        select([cache.c.value]).where(
            cache.c.key == key)).fetchone()

    if rv is None:
        raise KeyError

    return rv[0]


def set(con, cache, key, value, threshold):
    cnt = con.execute(
        select([func.count(cache)])).fetchone()[0]

    if cnt + 1 > threshold:
        con.execute(
            cache.delete().where(
                cache.c.key.in_(select(
                    [cache.c.key])
                    .order_by(cache.c.time)
                    .limit(1))))

    try:
        get(con, cache, key)
    except KeyError:
        insert = True
    else:
        insert = False

    if insert:
        stmt = cache.insert().values(key=key, value=value, time=time.time())
    else:
        stmt = cache.update().values(value=value, time=time.time()) \
                             .where(cache.c.key == key)

    con.execute(stmt)


def delete(con, cache, key):
    con.execute(cache.delete(cache.c.key == key))


class SACache(Base):
    """Implements cache using SQLAlchemy Core.
    """

    serialize = True

    def __init__(self, db, threshold=1024, timeout=-1):
        super(SACache, self).__init__(threshold, timeout)
        self.metadata = MetaData()
        self.engine = create_engine(db)

        self.cache = Table("cache", self.metadata,
            Column("key", String(255), primary_key=True),
            Column("value", LargeBinary(65535)),
            Column("time", Float))

        self.metadata.create_all(self.engine)

    def _get(self, ns, key):
        return get(self.engine.connect(), self.cache, ns + b'-' + key)

    def _set(self, ns, key, value):
        set(self.engine.connect(), self.cache, ns + b'-' + key, value, self.threshold)

    def _delete(self, ns, key):
        delete(self.engine.connect(), self.cache, ns + b'-' + key)
