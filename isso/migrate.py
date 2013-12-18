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

ns = '{http://disqus.com}'
dsq = '{http://disqus.com/disqus-internals}'

threads = set([])
comments = set([])


def insert(db, thread, posts):

    path = urlparse(thread.find('%slink' % ns).text).path
    remap = dict()

    if path not in db.threads:
        db.threads.new(path, thread.find('%stitle' % ns).text.strip())

    for item in sorted(posts, key=lambda k: k['created']):

        dsq_id = item.pop('dsq:id')
        item['parent'] = remap.get(item.pop('dsq:parent', None))
        rv = db.comments.add(path, item)
        remap[dsq_id] = rv["id"]

    comments.update(set(remap.keys()))


def disqus(db, xmlfile):

    if db.execute("SELECT * FROM comments").fetchone():
        if input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
            raise SystemExit("Abort.")

    tree = ElementTree.parse(xmlfile)
    res = defaultdict(list)

    for post in tree.findall('%spost' % ns):

        item = {
            'dsq:id': post.attrib.get(dsq + 'id'),
            'text': post.find('%smessage' % ns).text,
            'author': post.find('%sauthor/%sname' % (ns, ns)).text,
            'email': post.find('%sauthor/%semail' % (ns, ns)).text,
            'created': mktime(strptime(
                post.find('%screatedAt' % ns).text, '%Y-%m-%dT%H:%M:%SZ')),
            'remote_addr': '127.0.0.0',
            'mode': 1 if post.find("%sisDeleted" % ns).text == "false" else 4
        }

        if post.find(ns + 'parent') is not None:
            item['dsq:parent'] = post.find(ns + 'parent').attrib.get(dsq + 'id')

        res[post.find('%sthread' % ns).attrib.get(dsq + 'id')].append(item)

    num = len(tree.findall('%sthread' % ns))
    cols = int((os.popen('stty size', 'r').read() or "25 80").split()[1])

    for i, thread in enumerate(tree.findall('%sthread' % ns)):

        if int(round((i+1)/num, 2) * 100) % 13 == 0:

            sys.stdout.write("\r%s" % (" "*cols))
            sys.stdout.write("\r[%i%%]  %s" % (((i+1)/num * 100), thread.find('%sid' % ns).text))
            sys.stdout.flush()

        # skip (possibly?) duplicate, but empty thread elements
        if thread.find('%sid' % ns).text is None:
            continue

        id = thread.attrib.get(dsq + 'id')
        if id in res:
            threads.add(id)
            insert(db, thread, res[id])

    # in case a comment has been deleted (and no further childs)
    db.comments._remove_stale()

    sys.stdout.write("\r%s" % (" "*cols))
    sys.stdout.write("\r[100%%]  %i threads, %i comments\n" % (len(threads), len(comments)))

    orphans = set(map(lambda e: e.attrib.get(dsq + "id"), tree.findall("%spost" % ns))) - comments
    if orphans:
        print("Found %i orphans:" % len(orphans))
        for post in tree.findall("%spost" % ns):
            if post.attrib.get(dsq + "id") not in orphans:
                continue

            print(" * %s by %s <%s>" % (post.attrib.get(dsq + "id"),
                                        post.find("%sauthor/%sname" % (ns, ns)).text,
                                        post.find("%sauthor/%semail" % (ns, ns)).text))
            print(textwrap.fill(post.find("%smessage" % ns).text,
                                initial_indent="  ", subsequent_indent="  "))
            print("")
