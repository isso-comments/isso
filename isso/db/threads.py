# -*- encoding: utf-8 -*-


class Thread(object):

    def __init__(self, id, uri, title):
        self.id = id
        self.uri = uri
        self.title = title


class Threads(object):

    def __init__(self, db):

        self.db = db
        self.db.execute([
            'CREATE TABLE IF NOT EXISTS threads (',
            '    id INTEGER PRIMARY KEY, uri VARCHAR(256) UNIQUE, title VARCHAR(256))'])

    def __contains__(self, uri):
        return self.db.execute("SELECT title FROM threads WHERE uri=?", (uri, )) \
                      .fetchone() is not None

    def __getitem__(self, uri):
        return Thread(*self.db.execute("SELECT * FROM threads WHERE uri=?", (uri, )).fetchone())

    def new(self, uri, title):
        self.db.execute("INSERT INTO threads (uri, title) VALUES (?, ?)", (uri, title))
