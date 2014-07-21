# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import time

from sqlalchemy.sql import select, func


class Guard(object):

    def __init__(self, db, enabled, ratelimit=2, direct_reply=3,
                 reply_to_self=False, max_age=15*60):
        self.db = db
        self.enabled = enabled

        self.ratelimit = ratelimit
        self.direct_reply = direct_reply
        self.reply_to_self = reply_to_self
        self.max_age = max_age

    def validate(self, remote_addr, thread, comment):

        now = time.time()

        # block more than :param:`ratelimit` comments per minute
        count = self.db.engine.execute(
            select([func.count(self.db.comments)])
            .where(self.db.comments.c.remote_addr == remote_addr)
            .where(now - self.db.comments.c.created < 60)).fetchone()[0]

        if count >= self.ratelimit > -1:
            return False, "%s: ratelimit exceeded" % remote_addr

        # block more than three comments as direct response to the post
        if comment["parent"] is None:
            count = self.db.engine.execute(
                select([func.count(self.db.comments)])
                .where(self.db.comments.c.thread == thread.id)
                .where(self.db.comments.c.remote_addr == remote_addr)
                .where(self.db.comments.c.parent == None)).fetchone()[0]

            if count >= self.direct_reply:
                return False, "only {0} direct response(s) to {1}".format(
                    count, thread.uri)

        elif not self.reply_to_self:
            count = self.db.engine.execute(
                select([func.count(self.db.comments)])
                .where(self.db.comments.c.remote_addr == remote_addr)
                .where(now - self.db.comments.c.created < self.max_age)).fetchone()[0]

            if count > 0:
                return False, "editing frame is still open"

        return True, ""
