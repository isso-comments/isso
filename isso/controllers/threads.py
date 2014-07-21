# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

from isso.models import Thread


class Controller(object):

    def __init__(self, db):
        self.db = db

    def new(self, uri, title=None):
        _id = self.db.engine.execute(
            self.db.threads.insert().values(uri=uri, title=title)
        ).inserted_primary_key[0]

        return Thread(_id, uri, title)

    def get(self, uri):
        rv = self.db.engine.execute(
            self.db.threads.select(self.db.threads.c.uri == uri)).fetchone()

        if not rv:
            return None

        return Thread(*rv)

    def delete(self, uri):
        thread = self.get(uri)

        self.db.engine.execute(
            self.db.comments.delete().where(self.db.comments.c.thread == thread.id))

        self.db.engine.execute(
            self.db.threads.delete().where(self.db.threads.c.id == thread.id))
