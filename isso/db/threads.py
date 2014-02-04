# -*- encoding: utf-8 -*-

from sqlalchemy import Table, Column, Integer, String, select


def Thread(id, uri, title):
    return {
        "id": id,
        "uri": uri,
        "title": title
    }


class Threads:
    def __init__(self, db, metadata):
        self.db = db

        self.table = Table('threads', metadata,
                             Column('id', Integer, primary_key=True),
                             Column('uri', String(255), unique=True, nullable=False),
                             Column('title', String(255))
                             )

    def __contains__(self, uri):
        return self.db.execute(
            select([self.table.c.title], self.table.c.uri == uri)
        ).fetchone() is not None

    def __getitem__(self, uri):
        return Thread(*self.db.execute(self.table.select(self.table.c.uri == uri)).fetchone())

    def new(self, uri, title):
        self.db.execute(self.table.insert().values(uri=uri, title=title))
        return self[uri]
