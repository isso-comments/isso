# -*- encoding: utf-8 -*-

import sqlite3

class IssoDBException(Exception):
    pass

from isso.db.comments import Comments
from isso.db.threads import Threads


class SQLite3:

    def __init__(self, path, conf):

        self.path = path
        self.conf = conf
        self.mode = 1

        self.threads = Threads(self)
        self.comments = Comments(self)

    def execute(self, sql, args=()):

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        with sqlite3.connect(self.path) as con:
            return con.execute(sql, args)
