
import abc
import time
import sqlite3

from isso.models import Comment


class Abstract:

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def __init__(self, conf):
        return

    @abc.abstractmethod
    def add(path, comment):
        """Add a new comment to the database. Returns a Comment object."""
        return

    @abc.abstractmethod
    def update(self, path, id, comment):
        """
        Update an existing comment, but only writeable fields such as text,
        author, email, website and parent. This method should set the modified
        field to the current time.
        """
        return

    @abc.abstractmethod
    def delete(self, path, id):
        """
        Delete a comment. There are two distinctions: a comment is referenced
        by another valid comment's parent attribute or stand-a-lone. In this
        case the comment can't be removed without losing depending comments.
        Hence, delete removes all visible data such as text, author, email,
        website sets the mode field to 2.

        In the second case this comment can be safely removed without any side
        effects."""
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
        'id', 'path', 'created', 'modified',
        'text', 'author', 'email', 'website', 'parent', 'mode'
    ]

    def __init__(self, conf):

        self.dbpath = conf['SQLITE']
        self.mode = 1 if conf.get('MODERATION') else 0

        with sqlite3.connect(self.dbpath) as con:
            sql = ('main.comments (id INTEGER NOT NULL, path VARCHAR(255) NOT NULL,'
                   'created FLOAT NOT NULL, modified FLOAT, text VARCHAR,'
                   'author VARCHAR(64), email VARCHAR(64), website VARCHAR(64),'
                   'parent INTEGER, mode INTEGER, PRIMARY KEY (id, path))')
            con.execute("CREATE TABLE IF NOT EXISTS %s;" % sql)

            # increment id if (id, path) is no longer unique
            con.execute("""\
                CREATE TRIGGER IF NOT EXISTS increment AFTER INSERT ON comments
                BEGIN
                    UPDATE comments SET
                       id=(SELECT MAX(id)+1 FROM comments WHERE path=NEW.path)
                    WHERE rowid=NEW.rowid;
                END;""")

    def query2comment(self, query):
        if query is None:
            return None

        return Comment(
            text=query[4], author=query[5], email=query[6], website=query[7],
            parent=query[8], mode=query[9], id=query[0], created=query[2], modified=query[3]
        )

    def add(self, path, c):
        with sqlite3.connect(self.dbpath) as con:
            keys = ','.join(self.fields)
            values = ','.join('?'*len(self.fields))
            con.execute('INSERT INTO comments (%s) VALUES (%s);' % (keys, values), (
                0, path, c.created, c.modified, c.text, c.author, c.email, c.website,
                c.parent, self.mode)
            )

        with sqlite3.connect(self.dbpath) as con:
            return con.execute('SELECT path, MAX(id) FROM comments;').fetchone()

    def update(self, path, id, comment):
        with sqlite3.connect(self.dbpath) as con:
            for field, value in comment.iteritems(False):
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?;' % field,
                    (value, path, id))

        with sqlite3.connect(self.dbpath) as con:
            con.execute('UPDATE comments SET modified=? WHERE path=? AND id=?',
                (time.time(), path, id))
        return path, id

    def get(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            return self.query2comment(con.execute(
                'SELECT * FROM comments WHERE path=? AND id=?;', (path, id)).fetchone())

    def delete(self, path, id):
        with sqlite3.connect(self.dbpath) as con:
            con.execute('UPDATE comments SET text=? WHERE path=? AND id=?', ('', path, id))
            con.execute('UPDATE comments SET mode=? WHERE path=? AND id=?', (2, path, id))
            for field in set(Comment.fields) - set(['text', 'parent']):
                con.execute('UPDATE comments SET %s=? WHERE path=? AND id=?' % field,
                    (None, path, id))
        return path, id

    def retrieve(self, path, limit=20):
        with sqlite3.connect(self.dbpath) as con:
            rv = con.execute("SELECT * FROM comments WHERE path = ?" \
               + " ORDER BY id DESC LIMIT ?;", (path, limit)).fetchall()

        for item in rv:
            yield self.query2comment(item)
