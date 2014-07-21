# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import re
import time

from sqlalchemy.sql import func, select, not_

from isso.spam import Guard
from isso.utils import Bloomfilter
from isso.models import Comment

from isso.compat import string_types, buffer


class Invalid(Exception):
    pass


class Denied(Exception):
    pass


class Validator(object):

    # from Django appearently, looks good to me *duck*
    __url_re = re.compile(
        r'^'
        r'(https?://)?'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)'
        r'$', re.IGNORECASE)

    @classmethod
    def isurl(cls, text):
        return Validator.__url_re.match(text) is not None

    @classmethod
    def verify(cls, comment):

        if not isinstance(comment["parent"], (int, type(None))):
            return False, "parent must be an integer or null"

        if not isinstance(comment["text"], string_types):
            return False, "text must be a string"

        if len(comment["text"].rstrip()) < 3:
            return False, "text is too short (minimum length: 3)"

        for key in ("author", "email", "website"):
            if not isinstance(comment[key], (string_types, type(None))):
                return False, "%s must be a string or null" % key

        if len(comment["email"] or "") > 254:
            return False, "http://tools.ietf.org/html/rfc5321#section-4.5.3"

        if comment["website"]:
            if len(comment["website"]) > 254:
                return False, "arbitrary length limit"
            if not Validator.isurl(comment["website"]):
                return False, "Website not Django-conform"

        return True, ""


class Controller(object):

    def __init__(self, db, guard=None):
        if guard is None:
            guard = Guard(db, enabled=False)

        self.db = db
        self.guard = guard

    @classmethod
    def Comment(cls, rv):
        return Comment(
            id=rv[0], parent=rv[1], thread=rv[2], created=rv[3], modified=rv[4],
            mode=rv[5], remote_addr=rv[6], text=rv[7], author=rv[8], email=rv[9],
            website=rv[10], likes=rv[11], dislikes=rv[12], voters=Bloomfilter(bytearray(rv[13])))

    def new(self, remote_addr, thread, obj, moderated=False):
        obj.setdefault("text", "")
        obj.setdefault("parent", None)
        for field in ("email", "author", "website"):
            obj.setdefault(field, None)

        valid, reason = Validator.verify(obj)
        if not valid:
            raise Invalid(reason)

        if self.guard.enabled:
            valid, reason = self.guard.validate(remote_addr, thread, obj)
            if not valid:
                raise Denied(reason)

        obj["id"] = None
        obj["thread"] = thread.id
        obj["mode"] = 2 if moderated else 1
        obj["created"] = time.time()
        obj["modified"] = None
        obj["remote_addr"] = remote_addr

        obj["likes"] = obj["dislikes"] = 0
        obj["voters"] = Bloomfilter(iterable=[remote_addr])

        if obj["parent"] is not None:
            parent = self.get(obj["parent"])
            if parent is None:
                obj["parent"] = None
            elif parent.parent:  # normalize to max depth of 1
                obj["parent"] = parent.parent

        obj = Comment(**obj)
        _id = self.db.engine.execute(self.db.comments.insert()
            .values((obj.id, obj.parent, obj.thread, obj.created, obj.modified,
                     obj.mode, obj.remote_addr, obj.text, obj.author, obj.email,
                     obj.website, obj.likes, obj.dislikes, buffer(obj.voters.array)))
        ).inserted_primary_key[0]

        return obj.new(id=_id)

    def edit(self, _id, new):
        obj = self.get(_id)
        if not obj:
            return None

        new.setdefault("text", "")
        new.setdefault("parent", None)
        for field in ("email", "author", "website"):
            new.setdefault(field, None)

        valid, reason = Validator.verify(new)
        if not valid:
            raise Invalid(reason)

        obj = obj.new(text=new["text"], author=new["author"], email=new["email"],
                      website=new["website"], modified=time.time())
        self.db.engine.execute(self.db.comments.update()
            .values(text=obj.text, author=obj.author, email=obj.email,
                    website=obj.website, modified=obj.modified)
            .where(self.db.comments.c.id == _id))

        return obj

    def get(self, _id):
        """Retrieve comment with :param id: if any.
        """
        rv = self.db.engine.execute(
            self.db.comments.select(self.db.comments.c.id == _id)).fetchone()

        if not rv:
            return None

        return Controller.Comment(rv)

    def all(self, thread, mode=1, after=0, parent='any', order_by='id', limit=None):
        stmt = (self.db.comments.select()
            .where(self.db.comments.c.thread == thread.id)
            .where(self.db.comments.c.mode.op("|")(mode) == self.db.comments.c.mode)
            .where(self.db.comments.c.created > after))

        if parent != 'any':
            stmt = stmt.where(self.db.comments.c.parent == parent)

        stmt.order_by(getattr(self.db.comments.c, order_by))

        if limit:
            stmt.limit(limit)

        return list(map(Controller.Comment, self.db.engine.execute(stmt).fetchall()))

    def vote(self, remote_addr, _id, like):
        """Vote with +1 or -1 on comment :param id:

        Returns True on success (in either direction), False if :param
        remote_addr: has already voted. A comment can not be voted by its
        original author.
        """
        obj = self.get(_id)
        if obj is None:
            return False

        if remote_addr in obj.voters:
            return False

        if like:
            obj = obj.new(likes=obj.likes + 1)
        else:
            obj = obj.new(dislikes=obj.dislikes + 1)

        obj.voters.add(remote_addr)
        self.db.engine.execute(self.db.comments.update()
            .values(likes=obj.likes, dislikes=obj.dislikes,
                    voters=buffer(obj.voters.array))
            .where(self.db.comments.c.id == _id))

        return True

    def like(self, remote_addr, _id):
        return self.vote(remote_addr, _id, like=True)

    def dislike(self, remote_addr, _id):
        return self.vote(remote_addr, _id, like=False)

    def delete(self, _id):
        """
        Delete comment with :param id:

        If the comment is referenced by another (not yet deleted) comment, the
        comment is *not* removed, but cleared and flagged as deleted.
        """
        refs = self.db.engine.execute(
            self.db.comments.select(self.db.comments.c.id).where(
                self.db.comments.c.parent == _id)).fetchone()

        if refs is None:
            self.db.engine.execute(
                self.db.comments.delete(self.db.comments.c.id == _id))
            self.db.engine.execute(
                self.db.comments.delete()
                    .where(self.db.comments.c.mode.op("|")(4) == self.db.comments.c.mode)
                    .where(not_(self.db.comments.c.id.in_(
                        select([self.db.comments.c.parent]).where(
                            self.db.comments.c.parent != None)))))
            return None

        obj = self.get(_id)
        obj = obj.new(text="", author=None, email=None, website=None, mode=4)
        self.db.engine.execute(self.db.comments.update()
            .values(text=obj.text, author=obj.email, website=obj.website, mode=obj.mode)
            .where(self.db.comments.c.id == _id))

        return obj

    def count(self, *threads):
        """Retrieve comment count for :param threads:
        """

        ids = [getattr(th, "id", None) for th in threads]

        threads = dict(
            self.db.engine.execute(
                select([self.db.comments.c.thread, func.count(self.db.comments)])
                .where(self.db.comments.c.thread.in_(ids))
                .group_by(self.db.comments.c.thread)).fetchall())

        return [threads.get(_id, 0) for _id in ids]

    def reply_count(self, thread, mode=5, after=0):

        rv = self.db.engine.execute(
            select([self.db.comments.c.parent, func.count(self.db.comments)])
            .where(self.db.comments.c.thread == thread.id)
            # .where(self.db.comments.c.mode.op("|")(mode) == mode)
            .where(self.db.comments.c.created)
            .group_by(self.db.comments.c.parent)).fetchall()

        return dict(rv)

    def activate(self, _id):
        """Activate comment :param id: and return True on success.
        """
        obj = self.get(_id)
        if obj is None:
            return False

        i = self.db.engine.execute(self.db.comments.update()
            .values(mode=1)
            .where(self.db.comments.c.id == _id)
            .where(self.db.comments.c.mode == 2)).rowcount

        return i > 0

    def prune(self, delta):
        """Remove comments still in moderation queue older than max-age.
        """
        now = time.time()

        self.db.engine.execute(
            self.db.comments.delete()
            .where(self.db.comments.c.mode == 2)
            .where(now - self.db.comments.c.created > delta))

        return
