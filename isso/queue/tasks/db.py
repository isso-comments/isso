# -*- encoding: utf-8 -*-

import logging
log = logging.getLogger("isso")

from isso.controllers import threads, comments

from . import Cron


class Purge(Cron):

    def __init__(self, db, after):
        super(Purge, self).__init__(hours=1)
        self.after = after

        self.threads = threads.Controller(db)
        self.comments = comments.Controller(db)

    def run(self, data):
        rows = self.comments.prune(self.after)
        if rows:
            log.info("removed %s comment(s)", rows)

        rows = self.threads.prune()
        if rows:
            log.info("removed %s thread(s)", rows)
