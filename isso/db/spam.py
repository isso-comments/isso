# -*- encoding: utf-8 -*-

import time
import functools


class Guard:

    def __init__(self, db):

        self.db = db
        self.conf = db.conf.section("guard")

    def validate(self, uri, comment):

        if not self.conf.getboolean("enabled"):
            return True, ""

        for func in (self._limit, self._spam):
            valid, reason = func(uri, comment)
            if not valid:
                return False, reason
        return True, ""

    @classmethod
    def ids(cls, rv):
        return [str(col[0]) for col in rv]

    def _limit(self, uri, comment):

        # block more than :param:`ratelimit` comments per minute
        rv = self.db.execute([
            'SELECT id FROM comments WHERE remote_addr = ? AND ? - created < 60;'
        ], (comment["remote_addr"], time.time())).fetchall()

        if len(rv) >= self.conf.getint("ratelimit"):
            return False, "{0}: ratelimit exceeded ({1})".format(
                comment["remote_addr"], ', '.join(Guard.ids(rv)))

        # block more than three comments as direct response to the post
        if comment["parent"] is None:
            rv = self.db.execute([
                'SELECT id FROM comments WHERE',
                '    tid = (SELECT id FROM threads WHERE uri = ?)',
                'AND remote_addr = ?',
                'AND parent IS NULL;'
            ], (uri, comment["remote_addr"])).fetchall()

            if len(rv) >= self.conf.getint("direct-reply"):
                return False, "%i direct responses to %s" % (len(rv), uri)

        return True, ""

    def _spam(self, uri, comment):
        return True, ""
