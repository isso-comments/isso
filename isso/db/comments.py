# -*- encoding: utf-8 -*-

import time

from isso.utils import Bloomfilter
from isso.compat import buffer

from sqlalchemy import Table, Column, Integer, String, ForeignKey, Float, Text, LargeBinary, \
    select, func


class Comments:
    """Hopefully DB-independend SQL to store, modify and retrieve all
    comment-related actions.  Here's a short scheme overview:

        | tid (thread id) | id (comment id) | parent | ... | voters | remote_addr |
        +-----------------+-----------------+--------+-----+--------+-------------+
        | 1               | 1               | null   | ... | BLOB   | 127.0.0.0   |
        | 1               | 2               | 1      | ... | BLOB   | 127.0.0.0   |
        +-----------------+-----------------+--------+-----+--------+-------------+

    The tuple (tid, id) is unique and thus primary key.
    """

    fields = ['tid', 'id', 'parent', 'created', 'modified', 'mode', 'remote_addr',
              'text', 'author', 'email', 'website', 'likes', 'dislikes', 'voters']

    def __init__(self, db, metadata):
        self.db = db

        self.table = Table('comments', metadata,
                           Column('tid', ForeignKey("threads.id")),
                           Column('id', Integer, primary_key=True),
                           Column('parent', Integer),
                           Column('created', Float, nullable=False),
                           Column('modified', Float),
                           Column('mode', Integer),
                           Column('remote_addr', String(255)),
                           Column('text', Text),
                           Column('author', String(255)),
                           Column('email', String(255)),
                           Column('website', String(255)),
                           Column('likes', Integer, default=0),
                           Column('dislikes', Integer, default=0),
                           Column('voters', LargeBinary, nullable=False),
        )

    def add(self, uri, c):
        """
        Add new comment to DB and return a mapping of :attribute:`fields` and
        database values.
        """
        # self.db.execute([
        #                     'INSERT INTO comments (',
        #                     '    tid, parent,'
        #                     '    created, modified, mode, remote_addr,',
        #                     '    text, author, email, website, voters )',
        #                     'SELECT',
        #                     '    threads.id, ?,',
        #                     '    ?, ?, ?, ?,',
        #                     '    ?, ?, ?, ?, ?',
        #                     'FROM threads WHERE threads.uri = ?;'], (
        #                     c.get('parent'),
        #                     c.get('created') or time.time(), None, c["mode"], c['remote_addr'],
        #                     c['text'], c.get('author'), c.get('email'), c.get('website'), buffer(
        #                         Bloomfilter(iterable=[c['remote_addr']]).array),
        #                     uri)
        # )

        self.db.execute(self.table.insert().values(
            tid=self.db.threads[uri]['id'],
            parent=c.get('parent'),
            created=c.get('created') or time.time(),
            mode=c['mode'],
            remote_addr=c['remote_addr'],
            text=c['text'],
            author=c.get('author'),
            email=c.get('email'),
            website=c.get('website'),
            voters=buffer(Bloomfilter(iterable=[c['remote_addr']]).array),
        ))

        res = self.db.execute(select(self.table.columns, self.db.threads.table.c.uri == uri,
                                     from_obj=[self.table.join(self.db.threads.table)]))
        res = res.fetchone()

        return dict(zip(Comments.fields, res))

    def activate(self, id):
        """
        Activate comment id if pending.
        """
        self.db.execute([
                            'UPDATE comments SET',
                            '    mode=1',
                            'WHERE id=? AND mode=2'], (id, ))

    def update(self, id, data):
        """
        Update comment :param:`id` with values from :param:`data` and return
        updated comment.
        """
        self.db.execute([
                            'UPDATE comments SET',
                            ','.join(key + '=' + '?' for key in data),
                            'WHERE id=?;'],
                        list(data.values()) + [id])

        return self.get(id)

    def get(self, id):
        """
        Search for comment :param:`id` and return a mapping of :attr:`fields`
        and values.
        """
        rv = self.db.execute('SELECT * FROM comments WHERE id=?', (id, )).fetchone()
        if rv:
            return dict(zip(Comments.fields, rv))

        return None

    def fetch(self, uri, mode=5):
        """
        Return comments for :param:`uri` with :param:`mode`.
        """
        rv = self.db.execute([
                                 'SELECT comments.* FROM comments INNER JOIN threads ON',
                                 '    threads.uri=? AND comments.tid=threads.id AND (? | comments.mode) = ?'
                                 'ORDER BY id ASC;'], (uri, mode, mode)).fetchall()

        for item in rv:
            yield dict(zip(Comments.fields, item))

    def _remove_stale(self):

        sql = ('DELETE FROM',
               '    comments',
               'WHERE',
               '    mode=4 AND id NOT IN (',
               '        SELECT',
               '            parent',
               '        FROM',
               '            comments',
               '        WHERE parent IS NOT NULL)')

        while self.db.execute(sql).rowcount:
            continue

    def delete(self, id):
        """
        Delete a comment. There are two distinctions: a comment is referenced
        by another valid comment's parent attribute or stand-a-lone. In this
        case the comment can't be removed without losing depending comments.
        Hence, delete removes all visible data such as text, author, email,
        website sets the mode field to 4.

        In the second case this comment can be safely removed without any side
        effects."""

        refs = self.db.execute('SELECT * FROM comments WHERE parent=?', (id, )).fetchone()

        if refs is None:
            self.db.execute('DELETE FROM comments WHERE id=?', (id, ))
            self._remove_stale()
            return None

        self.db.execute('UPDATE comments SET text=? WHERE id=?', ('', id))
        self.db.execute('UPDATE comments SET mode=? WHERE id=?', (4, id))
        for field in ('author', 'website'):
            self.db.execute('UPDATE comments SET %s=? WHERE id=?' % field, (None, id))

        self._remove_stale()
        return self.get(id)

    def vote(self, upvote, id, remote_addr):
        """+1 a given comment. Returns the new like count (may not change because
        the creater can't vote on his/her own comment and multiple votes from the
        same ip address are ignored as well)."""

        rv = self.db.execute(select([self.table.c.likes, self.table.c.dislikes,
                                     self.table.c.voters], self.table.c.id == id)).fetchone()

        if rv is None:
            return None

        likes, dislikes, voters = rv
        if likes + dislikes >= 142:
            return {'likes': likes, 'dislikes': dislikes}

        bf = Bloomfilter(bytearray(voters), likes + dislikes)
        if remote_addr in bf:
            return {'likes': likes, 'dislikes': dislikes}

        bf.add(remote_addr)
        self.db.execute([
                            'UPDATE comments SET',
                            '    likes = likes + 1,' if upvote else 'dislikes = dislikes + 1,',
                            '    voters = ?'
                            'WHERE id=?;'], (buffer(bf.array), id))

        if upvote:
            return {'likes': likes + 1, 'dislikes': dislikes}
        return {'likes': likes, 'dislikes': dislikes + 1}

    def count(self, uri):
        """
        Return comment count for :param:`uri`.
        """

        # TODO: Does not work - no idea why
        # return self.db.execute(select([func.count(self.table.c.id)],
        #                               ((self.db.threads.table.c.uri == uri) & (
        #                                   self.table.c.mode == 1)),
        #                        from_obj=[self.table.join(self.db.threads.table)])).fetchone()

        join = [self.table.join(self.db.threads.table,
                                self.db.threads.table.c.id == self.table.c.tid)]
        query = select(
            [func.count(self.table.c.id)],
            ((self.db.threads.table.c.uri == uri) & (self.table.c.mode == 1)),
            from_obj=join
        )

        return self.db.execute(query).fetchone()[0]

        # [
        #     'SELECT COUNT(comments.id) FROM comments INNER JOIN threads ON',
        #     '    threads.uri=? AND comments.tid=threads.id AND comments.mode=1;'],
        # (uri, )).fetchone()

    def purge(self, delta):
        """
        Remove comments older than :param:`delta`.
        """
        self.db.execute([
                            'DELETE FROM comments WHERE mode = 2 AND ? - created > ?;'
                        ], (time.time(), delta))
        self._remove_stale()
