# -*- encoding: utf-8 -*-

import time

# A guard which uses database
class StatefulGuard:
    def __init__(self, db):

        self.db = db
        self.conf = db.conf.section("guard")
        self.max_age = db.conf.getint("general", "max-age")

    def validate(self, uri, comment):

        if not self.conf.getboolean("enabled"):
            return True, ""

        valid, reason = self._limit(uri, comment)
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

        # block replies to self unless :param:`reply-to-self` is enabled
        elif self.conf.getboolean("reply-to-self") is False:
            rv = self.db.execute([
                'SELECT id FROM comments WHERE'
                '    remote_addr = ?',
                'AND id = ?',
                'AND ? - created < ?'
            ], (comment["remote_addr"], comment["parent"],
                time.time(), self.max_age)).fetchall()

            if len(rv) > 0:
                return False, "edit time frame is still open"

        return True, ""
