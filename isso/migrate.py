# -*- encoding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import sys
import os
import io
import re
import logging
import textwrap
import functools

from time import mktime, strptime, time
from collections import defaultdict

from isso.utils import anonymize
from isso.compat import string_types

try:
    input = raw_input
except NameError:
    pass

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from xml.etree import ElementTree

logger = logging.getLogger("isso")


def strip(val):
    if isinstance(val, string_types):
        return val.strip()
    return val


class Progress(object):

    def __init__(self, end):
        self.end = end or 1

        self.istty = sys.stdout.isatty()
        self.last = 0

    def update(self, i, message):

        if not self.istty or message is None:
            return

        cols = int((os.popen('stty size', 'r').read()).split()[1])
        message = message[:cols - 7]

        if time() - self.last > 0.2:
            sys.stdout.write("\r{0}".format(" " * cols))
            sys.stdout.write("\r[{0:.0%}]  {1}".format(i/self.end, message))
            sys.stdout.flush()
            self.last = time()

    def finish(self, message):
        self.last = 0
        self.update(self.end, message + "\n")


class Disqus(object):

    ns = '{http://disqus.com}'
    internals = '{http://disqus.com/disqus-internals}'

    def __init__(self, db, xmlfile, empty_id=False):
        self.threads = set([])
        self.comments = set([])

        self.db = db
        self.xmlfile = xmlfile
        self.empty_id = empty_id

    def insert(self, thread, posts):

        path = urlparse(thread.find('%slink' % Disqus.ns).text).path
        remap = dict()

        if path not in self.db.threads:
            self.db.threads.new(path, thread.find(
                Disqus.ns + 'title').text.strip())

        for item in sorted(posts, key=lambda k: k['created']):

            dsq_id = item.pop('dsq:id')
            item['parent'] = remap.get(item.pop('dsq:parent', None))
            rv = self.db.comments.add(path, item)
            remap[dsq_id] = rv["id"]

        self.comments.update(set(remap.keys()))

    def migrate(self):

        tree = ElementTree.parse(self.xmlfile)
        res = defaultdict(list)

        for post in tree.findall(Disqus.ns + 'post'):

            item = {
                'dsq:id': post.attrib.get(Disqus.internals + 'id'),
                'text': post.find(Disqus.ns + 'message').text,
                'author': post.find('{0}author/{0}name'.format(Disqus.ns)).text,
                'email': post.find('{0}author/{0}email'.format(Disqus.ns)).text,
                'created': mktime(strptime(
                    post.find(Disqus.ns + 'createdAt').text, '%Y-%m-%dT%H:%M:%SZ')),
                'remote_addr': anonymize(post.find(Disqus.ns + 'ipAddress').text),
                'mode': 1 if post.find(Disqus.ns + "isDeleted").text == "false" else 4
            }

            if post.find(Disqus.ns + 'parent') is not None:
                item['dsq:parent'] = post.find(
                    Disqus.ns + 'parent').attrib.get(Disqus.internals + 'id')

            res[post.find('%sthread' % Disqus.ns).attrib.get(
                Disqus.internals + 'id')].append(item)

        progress = Progress(len(tree.findall(Disqus.ns + 'thread')))
        for i, thread in enumerate(tree.findall(Disqus.ns + 'thread')):
            progress.update(i, thread.find(Disqus.ns + 'id').text)

            # skip (possibly?) duplicate, but empty thread elements
            if thread.find(Disqus.ns + 'id').text is None and not self.empty_id:
                continue

            id = thread.attrib.get(Disqus.internals + 'id')
            if id in res:
                self.threads.add(id)
                self.insert(thread, res[id])

        # in case a comment has been deleted (and no further childs)
        self.db.comments._remove_stale()

        progress.finish("{0} threads, {1} comments".format(
            len(self.threads), len(self.comments)))

        orphans = set(map(lambda e: e.attrib.get(Disqus.internals + "id"),
                          tree.findall(Disqus.ns + "post"))) - self.comments
        if orphans and not self.threads:
            print("Isso couldn't import any thread, try again with --empty-id")
        elif orphans:
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


class WordPress(object):

    ns = "{http://wordpress.org/export/1.0/}"

    def __init__(self, db, xmlfile):
        self.db = db
        self.xmlfile = xmlfile
        self.count = 0

        for line in io.open(xmlfile, encoding="utf-8"):
            m = WordPress.detect(line)
            if m:
                self.ns = WordPress.ns.replace("1.0", m.group(1))
                break
        else:
            logger.warn("No WXR namespace found, assuming 1.0")

    def insert(self, thread):

        url = urlparse(thread.find("link").text)
        path = url.path

        if url.query:
            path += "?" + url.query

        self.db.threads.new(path, thread.find("title").text.strip())

        comments = list(map(self.Comment, thread.findall(self.ns + "comment")))
        comments.sort(key=lambda k: k["id"])

        remap = {}
        ids = set(c["id"] for c in comments)

        self.count += len(ids)

        while comments:
            for i, item in enumerate(comments):
                if item["parent"] in ids:
                    continue

                item["parent"] = remap.get(item["parent"], None)
                rv = self.db.comments.add(path, item)
                remap[item["id"]] = rv["id"]

                ids.remove(item["id"])
                comments.pop(i)

                break
            else:
                # should never happen, but... it's WordPress.
                return

    def migrate(self):

        tree = ElementTree.parse(self.xmlfile)

        skip = 0
        items = tree.findall("channel/item")

        progress = Progress(len(items))
        for i, thread in enumerate(items):
            if thread.find("title").text is None or thread.find(self.ns + "comment") is None:
                skip += 1
                continue

            progress.update(i, thread.find("title").text)
            self.insert(thread)

        progress.finish("{0} threads, {1} comments".format(
            len(items) - skip, self.count))

    def Comment(self, el):
        return {
            "text": strip(el.find(self.ns + "comment_content").text),
            "author": strip(el.find(self.ns + "comment_author").text),
            "email": strip(el.find(self.ns + "comment_author_email").text),
            "website": strip(el.find(self.ns + "comment_author_url").text),
            "remote_addr": anonymize(
                strip(el.find(self.ns + "comment_author_IP").text)),
            "created": mktime(strptime(
                strip(el.find(self.ns + "comment_date_gmt").text),
                "%Y-%m-%d %H:%M:%S")),
            "mode": 1 if el.find(self.ns + "comment_approved").text == "1" else 2,
            "id": int(el.find(self.ns + "comment_id").text),
            "parent": int(el.find(self.ns + "comment_parent").text) or None
        }

    @classmethod
    def detect(cls, peek):
        return re.compile("http://wordpress.org/export/(1\.\d)/").search(peek)


def autodetect(peek):

    if 'xmlns="http://disqus.com' in peek:
        return Disqus

    m = WordPress.detect(peek)
    if m:
        return WordPress

    return None


def dispatch(type, db, dump, empty_id=False):
    if db.execute("SELECT * FROM comments").fetchone():
        if input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
            raise SystemExit("Abort.")

    if type == "disqus":
        cls = Disqus
    elif type == "wordpress":
        cls = WordPress
    else:
        with io.open(dump, encoding="utf-8") as fp:
            cls = autodetect(fp.read(io.DEFAULT_BUFFER_SIZE))

    if cls is None:
        raise SystemExit("Unknown format, abort.")

    if cls is Disqus:
        cls = functools.partial(cls, empty_id=empty_id)

    cls(db, dump).migrate()
