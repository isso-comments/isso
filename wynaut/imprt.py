# -*- encoding: utf-8 -*-

from __future__ import division

import sys
import os
import time
import tempfile
import textwrap

from time import mktime, strptime
from xml.etree import ElementTree
from collections import defaultdict

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

try:
    input = raw_input
except NameError:
    pass

from werkzeug.utils import cached_property

from isso.db import SQLite3
from isso.core import Config

from wynaut import get_parser


class Import(object):

    def __init__(self):

        self.last = 0

        try:
            self.cols = int(os.popen('stty size', 'r').read().split()[1])
        except IndexError:
            self.cols = 25

    def progress(self, current, max, msg):

        if time.time() - self.last < 0.1:
            return

        sys.stdout.write("\r{0}".format(" "*self.cols))
        sys.stdout.write("\r[{0:.3}%]  {1:.{2}}".format(
            current/max*100, msg.strip(), self.cols - 9))
        sys.stdout.flush()

        self.last = time.time()

    def done(self, msg):
        sys.stdout.write("\r{0}".format(" "*self.cols))
        sys.stdout.write("\r[100%]  {0}\n".format(msg.strip()))
        sys.stdout.flush()


class Disqus(Import):

    ns = '{http://disqus.com}'
    internals = '{http://disqus.com/disqus-internals}'

    def __init__(self, xmlfile):

        super(Disqus, self).__init__()
        self.tree = ElementTree.parse(xmlfile)

        self._threads = set([])
        self._posts = set([])


    @cached_property
    def threads(self):
        return [thr for thr in self.tree.findall("{0}thread".format(Disqus.ns))
                            if thr.find("{0}id".format(Disqus.ns)).text is not None]

    @cached_property
    def posts(self):
        return self.tree.findall("{0}post".format(Disqus.ns))

    def migrate(self, db):

        # map thread id to list of posts
        rv = defaultdict(list)

        for post in self.posts:

            item = {
                'dsq:id': post.attrib.get(Disqus.internals + 'id'),
                'text': post.find('%smessage' % Disqus.ns).text,
                'author': post.find('{0}author/{0}name'.format(Disqus.ns)).text,
                'email': post.find('{0}author/{0}email'.format(Disqus.ns)).text,
                'created': mktime(strptime(
                    post.find('%screatedAt' % Disqus.ns).text, '%Y-%m-%dT%H:%M:%SZ')),
                'remote_addr': '127.0.0.0',
                'mode': 1 if post.find("%sisDeleted" % Disqus.ns).text == "false" else 4
            }

            if post.find(Disqus.ns + 'parent') is not None:
                item['dsq:parent'] = post.find(Disqus.ns + 'parent').attrib.get(Disqus.internals + 'id')

            rv[post.find('%sthread' % Disqus.ns).attrib.get(Disqus.internals + 'id')].append(item)

        for i, thread in enumerate(self.threads):

            self.progress(i, len(self.threads), thread.find('{0}id'.format(Disqus.ns)).text)

            # skip (possibly?) duplicate, but empty thread elements
            if thread.find('%sid' % Disqus.ns).text is None:
                continue

            id = thread.attrib.get(Disqus.internals + 'id')
            if id in rv:
                self._threads.add(id)
                self._insert(db, thread, rv[id])

        # in case a comment has been deleted (and no further childs)
        db.comments._remove_stale()

        self.done("{0} threads, {1} comments".format(len(self._threads), len(self._posts)))

        orphans = set(map(lambda e: e.attrib.get(Disqus.internals + "id"), self.posts)) - self._posts
        if orphans:
            print("Found %i orphans:" % len(orphans))
            for post in self.posts:
                if post.attrib.get(Disqus.internals + "id") not in orphans:
                    continue

                print(" * %s by %s <%s>" % (post.attrib.get(Disqus.internals + "id"),
                                            post.find("{0}author/{0}name".format(Disqus.ns)).text,
                                            post.find("{0}author/{0}email".format(Disqus.ns)).text))
                print(textwrap.fill(post.find("%smessage" % Disqus.ns).text,
                                    initial_indent="  ", subsequent_indent="  "))

    def _insert(self, db, thread, posts):

        path = urlparse(thread.find('%slink' % Disqus.ns).text).path
        remap = dict()

        if path not in db.threads:
            db.threads.new(path, thread.find('%stitle' % Disqus.ns).text.strip())

        for item in sorted(posts, key=lambda k: k['created']):

            dsq_id = item.pop('dsq:id')
            item['parent'] = remap.get(item.pop('dsq:parent', None))
            rv = db.comments.add(path, item)
            remap[dsq_id] = rv["id"]

        self._posts.update(set(remap.keys()))


def main():

    parser = get_parser("import Disqus XML export")
    parser.add_argument("dump", metavar="FILE")
    parser.add_argument("-y", "--yes", dest="yes", action="store_true",
        help="always confirm actions")
    parser.add_argument("-n", "--dry-run", dest="dryrun", action="store_true",
        help="perform a trial run with no changes made")
    parser.add_argument("-f", "--from", dest="type", choices=["disqus", "csv"])

    args = parser.parse_args()
    conf = Config.load(args.conf)

    xxx = tempfile.NamedTemporaryFile()
    dbpath = conf.get("general", "dbpath") if not args.dryrun else xxx.name

    if args.type == "disqus":
        importer = Disqus(args.dump)
    elif args.type == "csv":
        pass

    db = SQLite3(dbpath, conf)

    if db.execute("SELECT * FROM comments").fetchone():
        if not args.yes and input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
            raise SystemExit("Abort.")

    importer.migrate(db)
