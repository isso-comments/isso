# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py
#
# TODO
#
# - export does not include website from commenters
# - Disqus includes already deleted comments

from time import mktime, strptime
from urlparse import urlparse
from collections import defaultdict

from xml.etree import ElementTree

from isso.models import Comment


ns = '{http://disqus.com}'
dsq = '{http://disqus.com/disqus-internals}'


def insert(db, thread, comments):

    path = urlparse(thread.find('%sid' % ns).text).path
    remap = dict()

    for item in sorted(comments, key=lambda k: k['created']):

        parent = remap.get(item.get('dsq:parent'))
        comment = Comment(created=item['created'], text=item['text'],
                          author=item['author'], email=item['email'], parent=parent)

        rv = db.add(path, comment)
        remap[item['dsq:id']] = rv.id


def disqus(db, xml):

    tree = ElementTree.fromstring(xml)
    res = defaultdict(list)

    for post in tree.findall('%spost' % ns):

        item = {
            'dsq:id': post.attrib.get(dsq + 'id'),
            'text': post.find('%smessage' % ns).text,
            'author': post.find('%sauthor/%sname' % (ns, ns)).text,
            'email': post.find('%sauthor/%semail' % (ns, ns)).text,
            'created': mktime(strptime(
                post.find('%screatedAt' % ns).text, '%Y-%m-%dT%H:%M:%SZ'))
        }

        if post.find(ns + 'parent') is not None:
            item['dsq:parent'] = post.find(ns + 'parent').attrib.get(dsq + 'id')

        res[post.find('%sthread' % ns).attrib.get(dsq + 'id')].append(item)

    for thread in tree.findall('%sthread' % ns):
        id = thread.attrib.get(dsq + 'id')
        if id in res:
            insert(db, thread, res[id])
