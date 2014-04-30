# -*- encoding: utf-8 -*-

from __future__ import division

import sys
import os
import textwrap

from time import mktime, strptime
from collections import defaultdict

try:
    input = raw_input
except NameError:
    pass

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from xml.etree import ElementTree


class Disqus(object):

    ns = '{http://disqus.com}'
    internals = '{http://disqus.com/disqus-internals}'

    def __init__(self, db, xmlfile):
        self.threads = set([])
        self.comments = set([])

        self.db = db
        self.xmlfile = xmlfile

    def insert(self, thread, posts):

        path = urlparse(thread.find('%slink' % Disqus.ns).text).path
        remap = dict()

        if path not in self.db.threads:
            self.db.threads.new(path, thread.find(Disqus.ns + 'title').text.strip())

        for item in sorted(posts, key=lambda k: k['created']):

            dsq_id = item.pop('dsq:id')
            item['parent'] = remap.get(item.pop('dsq:parent', None))
            rv = self.db.comments.add(path, item)
            remap[dsq_id] = rv["id"]

        self.comments.update(set(remap.keys()))

    def migrate(self):

        tree = ElementTree.parse(self.xmlfile)
        res = defaultdict(list)

        for post in tree.findall('%spost' % Disqus.ns):

            item = {
                'dsq:id': post.attrib.get(Disqus.internals + 'id'),
                'text': post.find(Disqus.ns + 'message').text,
                'author': post.find('{0}author/{0}name'.format(Disqus.ns)).text,
                'email': post.find('{0}author/{0}email'.format(Disqus.ns)).text,
                'created': mktime(strptime(
                    post.find(Disqus.ns + 'createdAt').text, '%Y-%m-%dT%H:%M:%SZ')),
                'remote_addr': '127.0.0.0',
                'mode': 1 if post.find(Disqus.ns + "isDeleted").text == "false" else 4
            }

            if post.find(Disqus.ns + 'parent') is not None:
                item['dsq:parent'] = post.find(Disqus.ns + 'parent').attrib.get(Disqus.internals + 'id')

            res[post.find('%sthread' % Disqus.ns).attrib.get(Disqus.internals + 'id')].append(item)

        num = len(tree.findall(Disqus.ns + 'thread'))
        cols = int((os.popen('stty size', 'r').read() or "25 80").split()[1])

        for i, thread in enumerate(tree.findall(Disqus.ns + 'thread')):

            if int(round((i+1)/num, 2) * 100) % 13 == 0:
                sys.stdout.write("\r%s" % (" "*cols))
                sys.stdout.write("\r[%i%%]  %s" % (((i+1)/num * 100), thread.find(Disqus.ns + 'id').text))
                sys.stdout.flush()

            # skip (possibly?) duplicate, but empty thread elements
            if thread.find(Disqus.ns + 'id').text is None:
                continue

            id = thread.attrib.get(Disqus.internals + 'id')
            if id in res:
                self.threads.add(id)
                self.insert(thread, res[id])

        # in case a comment has been deleted (and no further childs)
        self.db.comments._remove_stale()

        sys.stdout.write("\r%s" % (" "*cols))
        sys.stdout.write("\r[100%]  {0} threads, {1} comments\n".format(
            len(self.threads), len(self.comments)))

        orphans = set(map(lambda e: e.attrib.get(Disqus.internals + "id"), tree.findall(Disqus.ns + "post"))) - self.comments
        if orphans:
            print("Found %i orphans:" % len(orphans))
            for post in tree.findall(Disqus.ns + "post"):
                if post.attrib.get(Disqus.internals + "id") not in orphans:
                    continue

                print(" * {0} by {1} <{2}>".format(
                    post.attrib.get(Disqus.internals + "id"),
                    post.find("{0}author/{0}name".format(Disqus.ns)).text,
                    post.find("{0}author/{0}email".format(Disqus.ns)).text))
                print(textwrap.fill(post.find(Disqus.ns + "message").text,
                                    initial_indent="  ", subsequent_indent="  "))
                print("")


def dispatch(db, dump):
        if db.execute("SELECT * FROM comments").fetchone():
            if input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
                raise SystemExit("Abort.")

        Disqus(db, dump).migrate()
