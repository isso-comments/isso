# -*- encoding: utf-8 -*-

import sqlite3

from isso.db.comments import Comments
from isso.db.threads import Threads
from isso.db.spam import Guard


class SQLite3:

    def __init__(self, path, conf):

        self.path = path
        self.conf = conf
        self.mode = 1

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

        if isinstance(sql, (list, tuple)):
            sql = ' '.join(sql)

        with sqlite3.connect(self.path) as con:
            return con.execute(sql, args)
