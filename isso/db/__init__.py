# -*- encoding: utf-8 -*-

import sqlite3

from isso.db.comments import Comments
from isso.db.threads import Threads


class SQLite3:

    connection = None

    def __init__(self, path, moderation=False):

        self.path = path
        self.mode = 2 if moderation else 1

        self.threads = Threads(self)
        self.comments = Comments(self)

    def execute(self, sql, args=()):

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        with sqlite3.connect(self.path) as con:
            return con.execute(sql, args)
