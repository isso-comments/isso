# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import operator


class Thread(object):

    __slots__ = ['id', 'uri', 'title']

    def __init__(self, id, uri, title=None):
        self.id = id
        self.uri = uri
        self.title = title


class Comment(object):

    __slots__ = [
        'id', 'parent', 'thread', 'created', 'modified', 'mode', 'remote_addr',
        'text', 'author', 'email', 'website', 'likes', 'dislikes', 'voters']

    def __init__(self, **kwargs):
        for attr in Comment.__slots__:
            try:
                setattr(self, attr, kwargs.pop(attr))
            except KeyError:
                raise TypeError("missing '{0}' argument".format(attr))

        if kwargs:
            raise TypeError("unexpected argument '{0}'".format(*kwargs.popitem()))

    def new(self, **kwargs):
        kw = dict(zip(Comment.__slots__, operator.attrgetter(*Comment.__slots__)(self)))
        kw.update(kwargs)
        return Comment(**kw)

    @property
    def moderated(self):
        return self.mode | 2 == self.mode

    @property
    def deleted(self):
        return self.mode | 4 == self.mode
