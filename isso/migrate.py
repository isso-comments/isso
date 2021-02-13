# -*- encoding: utf-8 -*-

from __future__ import division, print_function, unicode_literals

import functools
import io
import json
import logging
import os
import re
import sys
import textwrap

from time import mktime, strptime, time
from collections import defaultdict

from isso.utils import anonymize

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
    if isinstance(val, (str, )):
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
            sys.stdout.write("\r[{0:.0%}]  {1}".format(i / self.end, message))
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
            email = post.find('{0}author/{0}email'.format(Disqus.ns))
            ip = post.find(Disqus.ns + 'ipAddress')

            item = {
                'dsq:id': post.attrib.get(Disqus.internals + 'id'),
                'text': post.find(Disqus.ns + 'message').text,
                'author': post.find('{0}author/{0}name'.format(Disqus.ns)).text,
                'email': email.text if email is not None else '',
                'created': mktime(strptime(
                    post.find(Disqus.ns + 'createdAt').text, '%Y-%m-%dT%H:%M:%SZ')),
                'remote_addr': anonymize(ip.text if ip is not None else '0.0.0.0'),
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

                email = post.find("{0}author/{0}email".format(Disqus.ns))
                print(" * {0} by {1} <{2}>".format(
                    post.attrib.get(Disqus.internals + "id"),
                    post.find("{0}author/{0}name".format(Disqus.ns)).text,
                    email.text if email is not None else ""))
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
        return re.compile("http://wordpress.org/export/(1\\.\\d)/").search(peek)


class Generic(object):
    """A generic importer.

    The source format is a json with the following format:

    A list of threads, each item being a dict with the following data:

        - id: a text representing the unique thread id
        - title: the title of the thread
        - comments: the list of comments

    Each item in that list of comments is a dict with the following data:

        - id: an integer with the unique id of the comment inside the thread (it can be repeated
          among different threads); this will be used to order the comment inside the thread
        - author: the author's name
        - email: the author's email
        - website: the author's website
        - remote_addr: the author's IP
        - created: a timestamp, in the format "%Y-%m-%d %H:%M:%S"
    """

    def __init__(self, db, json_file):
        self.db = db
        self.json_file = json_file
        self.count = 0

    def insert(self, thread):
        """Process a thread and insert its comments in the DB."""
        thread_id = thread['id']
        title = thread['title']
        self.db.threads.new(thread_id, title)

        comments = list(map(self._build_comment, thread['comments']))
        comments.sort(key=lambda comment: comment['id'])
        self.count += len(comments)
        for comment in comments:
            self.db.comments.add(thread_id, comment)

    def migrate(self):
        """Process the input file and fill the DB."""
        with io.open(self.json_file, 'rt', encoding='utf8') as fh:
            threads = json.load(fh)
        progress = Progress(len(threads))

        for i, thread in enumerate(threads):
            progress.update(i, str(i))
            self.insert(thread)

        progress.finish("{0} threads, {1} comments".format(len(threads), self.count))

    def _build_comment(self, raw_comment):
        return {
            "text": raw_comment['text'],
            "author": raw_comment['author'],
            "email": raw_comment['email'],
            "website": raw_comment['website'],
            "created": mktime(strptime(raw_comment['created'], "%Y-%m-%d %H:%M:%S")),
            "mode": 1,
            "id": int(raw_comment['id']),
            "parent": None,
            "remote_addr": raw_comment["remote_addr"],
        }

    @classmethod
    def detect(cls, peek):
        """Return if peek looks like the beginning of a JSON file.

        Note that we can not check the JSON properly as we only receive here
        the original file truncated.
        """
        return peek.startswith("[{")


def autodetect(peek):

    if 'xmlns="http://disqus.com' in peek:
        return Disqus

    m = WordPress.detect(peek)
    if m:
        return WordPress

    if Generic.detect(peek):
        return Generic

    return None


def dispatch(type, db, dump, empty_id=False):
    if db.execute("SELECT * FROM comments").fetchone():
        if input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
            raise SystemExit("Abort.")

    if type == "disqus":
        cls = Disqus
    elif type == "wordpress":
        cls = WordPress
    elif type == "generic":
        cls = Generic
    else:
        with io.open(dump, encoding="utf-8") as fp:
            cls = autodetect(fp.read(io.DEFAULT_BUFFER_SIZE))

    if cls is None:
        raise SystemExit("Unknown format, abort.")

    if cls is Disqus:
        cls = functools.partial(cls, empty_id=empty_id)

    cls(db, dump).migrate()
