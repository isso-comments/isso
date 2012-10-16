
import abc
import time
import sqlite3

from os.path import join

from isso.comments import Comment


class Abstract:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def initialize(self, conf):
        return

    @abc.abstractmethod
    def shutdown(self):
        return

    @abc.abstractmethod
    def add(path, comment):
        return

    @abc.abstractmethod
    def update(self, path, comment):
        return

    @abc.abstractmethod
    def delete(self, path, comment):
        return

    @abc.abstractmethod
    def retrieve(self, path, limit=20):
        return


class SQLite(Abstract):
    """A basic :class:`Abstract` implementation using SQLite3.  All comments
    share a single database. The tuple (id, path) acts as unique identifier
    for a comment. Multiple comments per path (= that is the URI to your blog
    post) are ordered by that id."""

    fields = [
        'id', 'path', 'timestamp',
        'text', 'author', 'email', 'website', 'parent', 'mode'
    ]

    def initialize(self, conf):

        self.dbpath = conf['SQLITE']
        self.mode = 1 if conf.get('MODERATION') else 0

        with sqlite3.connect(self.dbpath) as con:
            sql = ('main.comments (id INTEGER NOT NULL, path VARCHAR(255) NOT NULL,'
                   'timestamp FLOAT NOT NULL, text VARCHAR, author VARCHAR(64),'
                   'email VARCHAR(64), website VARCHAR(64), parent INTEGER, mode INTEGER,'
                   'PRIMARY KEY (id, path))')
            con.execute("CREATE TABLE IF NOT EXISTS %s;" % sql)

            # increment id if (id, path) is no longer unique
            con.execute("""\
                CREATE TRIGGER IF NOT EXISTS increment AFTER INSERT ON comments
                BEGIN
                    UPDATE comments SET
                       id=(SELECT MAX(id)+1 FROM comments WHERE path=NEW.path)
                    WHERE rowid=NEW.rowid;
                END;""")

    def shutdown(self):
        return

    def query2comment(self, query):
        return Comment(
            text=query[3], author=query[4], email=query[5], website=query[6],
            parent=query[7], timestamp=query[2], id=query[0], mode=query[8]
        )

    def add(self, path, c):
        with sqlite3.connect(self.dbpath) as con:
            keys = ','.join(self.fields)
            values = ','.join('?'*len(self.fields))
            con.execute('INSERT INTO comments (%s) VALUES (%s);' % (keys, values), (
                0, path, time.time(), c.text, c.author, c.email, c.website,
                c.parent, self.mode)
            )

    def update(self, path, comment):
        return

    def delete(self, path, comment):
        return

    def retrieve(self, path, limit=20):
        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute("SELECT * FROM comments WHERE path = ?" \
               + " ORDER BY id DESC;", (path, )).fetchall()

        for item in rv:
            yield self.query2comment(item)
