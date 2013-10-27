# -*- encoding: utf-8 -*-

import time

from isso.db import IssoDBException


class TooManyComments(IssoDBException):
    pass


def check(func):

    def dec(self, uri, c):

        if not self.db.conf.getboolean("guard", "enabled"):
            return func(self, uri, c)

        # block more than two comments per minute
        rv = self.db.execute([
            'SELECT id FROM comments WHERE remote_addr = ? AND created > ?;'
        ], (c["remote_addr"], time.time() + 60)).fetchall()

        if len(rv) >= self.db.conf.getint("guard", "ratelimit"):
            raise TooManyComments

        # block more than three comments as direct response to the post
        rv = self.db.execute([
            'SELECT id FROM comments WHERE remote_addr = ? AND parent IS NULL;'
        ], (c["remote_addr"], )).fetchall()

        if len(rv) >= 3:
            raise TooManyComments

        # block reply to own comment if the cookie is still available (max age)
        if "parent" in c:
            rv = self.db.execute([
                'SELECT id FROM comments WHERE remote_addr = ? AND id = ? AND ? - created < ?;'
            ], (c["remote_addr"], c["parent"], time.time(),
                self.db.conf.getint("general", "max-age"))).fetchall()

            if len(rv) > 0:
                raise TooManyComments

        return func(self, uri, c)

    return dec
