# -*- encoding: utf-8 -*-

from isso.controllers import comments

from . import Cron


class Purge(Cron):

    def __init__(self, db, after):
        super(Purge, self).__init__(hours=1)
        self.comments = comments.Controller(db)
        self.after = after

    def run(self, data):
        self.comments.purge(self.after)
