# -*- encoding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import time

from sqlalchemy.sql import select, func

from . import Base


class SACache(Base):
    """Implements cache using SQLAlchemy Core.

    JSON is used for safe serialization of python primitives.
    """

    serialize = True

    def __init__(self, db, threshold=1024, timeout=-1):
        super(SACache, self).__init__(threshold, timeout)
        self.db = db

    def _get(self, ns, key):
        rv = self.db.engine.execute(
            select([self.db.cache.c.value]).where(
                self.db.cache.c.key == ns + b'-' + key)).fetchone()

        if rv is None:
            raise KeyError

        return rv[0]

    def _set(self, ns, key, value):
        with self.db.transaction:
            cnt = self.db.engine.execute(
                select([func.count(self.db.cache)])).fetchone()[0]

            if cnt + 1 > self.threshold:
                self.db.engine.execute(
                    self.db.cache.delete().where(
                        self.db.cache.c.key.in_(select(
                            [self.db.cache.c.key])
                            .order_by(self.db.cache.c.time)
                            .limit(1))))

            try:
                self._get(ns, key)
            except KeyError:
                insert = True
            else:
                insert = False

            if insert:
                stmt = self.db.cache.insert().values(
                    key=ns + b'-' + key, value=value, time=time.time())
            else:
                stmt = self.db.cache.update().values(
                    value=value, time=time.time()).where(
                        self.db.cache.c.key == ns + b'-' + key)

            self.db.engine.execute(stmt)

    def _delete(self, ns, key):
        with self.db.transaction:
            self.db.engine.execute(
                self.db.cache.delete(self.db.cache.c.key == ns + b'-' + key))
