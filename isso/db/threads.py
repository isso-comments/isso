# -*- encoding: utf-8 -*-


def Thread(id, uri, title, read_only=False):
    return {"id": id, "uri": uri, "title": title, "read_only": bool(read_only)}


class Threads(object):
    def __init__(self, db):
        self.db = db
        self.db.execute(
            [
                "CREATE TABLE IF NOT EXISTS threads (",
                "    id INTEGER PRIMARY KEY, uri VARCHAR(256) UNIQUE, title VARCHAR(256),",
                "    read_only INTEGER DEFAULT 0)",
            ]
        )

    def __contains__(self, uri):
        return self.db.execute("SELECT title FROM threads WHERE uri=?", (uri,)).fetchone() is not None

    def __getitem__(self, uri):
        return Thread(*self.db.execute("SELECT * FROM threads WHERE uri=?", (uri,)).fetchone())

    def get(self, id):
        return Thread(*self.db.execute("SELECT * FROM threads WHERE id=?", (id,)).fetchone())

    def new(self, uri, title):
        self.db.execute("INSERT INTO threads (uri, title) VALUES (?, ?)", (uri, title))
        return self[uri]

    def set_read_only(self, uri, read_only):
        self.db.execute(
            "UPDATE threads SET read_only=? WHERE uri=?",
            (int(read_only), uri),
        )

    def get_read_only(self, uri):
        """Return the thread's read-only flag, or ``False`` for an unknown uri."""
        rv = self.db.execute("SELECT read_only FROM threads WHERE uri=?", (uri,)).fetchone()
        return bool(rv[0]) if rv else False

    def fetchall(self):
        """
        Return all threads with their comment count, for the admin interface.
        """
        rv = self.db.execute(
            [
                "SELECT threads.id, threads.uri, threads.title, threads.read_only,",
                "    COUNT(comments.id) AS comment_count",
                "FROM threads LEFT OUTER JOIN comments ON comments.tid = threads.id",
                "GROUP BY threads.id ORDER BY threads.id DESC",
            ]
        ).fetchall()
        for id, uri, title, read_only, comment_count in rv:
            yield dict(Thread(id, uri, title, read_only), comment_count=comment_count)
