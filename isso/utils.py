# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from __future__ import division

import json

import socket
import httplib

import random
import hashlib

from string import ascii_letters, digits
from urlparse import urlparse
from contextlib import closing

import html5lib
import ipaddress

from isso.models import Comment


class IssoEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Comment):
            return dict((field, value) for field, value in obj.iteritems())

        return json.JSONEncoder.default(self, obj)


def urlexists(host, path):

    rv = urlparse(host)
    http = httplib.HTTPSConnection if rv.scheme == 'https' else httplib.HTTPConnection

    with closing(http(rv.netloc, rv.port, timeout=3)) as con:
        try:
            con.request('HEAD', path)
        except (httplib.HTTPException, socket.error):
            return False
        return con.getresponse().status == 200


def heading(host, path):
    """Connect to `host`, GET path and start from #isso-thread to search for
    a possible heading (h1). Returns `None` if nothing found."""

    rv = urlparse(host)
    http = httplib.HTTPSConnection if rv.scheme == 'https' else httplib.HTTPConnection

    with closing(http(rv.netloc, rv.port, timeout=15)) as con:
        con.request('GET', path)
        html = html5lib.parse(con.getresponse().read(), treebuilder="dom")

    assert html.lastChild.nodeName == "html"
    html = html.lastChild

    # aka getElementById
    el = list(filter(lambda i: i.attributes["id"].value == "isso-thread",
              filter(lambda i: i.attributes.has_key("id"), html.getElementsByTagName("div"))))

    if not el:
        return None

    el = el[0]
    visited = []

    def recurse(node):
        for child in node.childNodes:
            if child.nodeType != child.ELEMENT_NODE:
                continue
            if child.nodeName.upper() == "H1":
                return child
            if child not in visited:
                return recurse(child)

    def gettext(rv):
        for child in rv.childNodes:
            if child.nodeType == child.TEXT_NODE:
                yield child.nodeValue
            if child.nodeType == child.ELEMENT_NODE:
                for item in gettext(child):
                    yield item

    while el is not None:  # el.parentNode is None in the very end

        visited.append(el)
        rv = recurse(el)

        if rv:
            return ''.join(gettext(rv)).strip()

        el = el.parentNode

    return None


def anonymize(remote_addr):
    ip = ipaddress.ip_address(remote_addr)
    if ip.version == "4":
        return ''.join(ip.exploded.rsplit('.', 1)[0]) + '.' + '0'
    return ip.exploded.rsplit(':', 5)[0]


def salt(value, s=u'\x082@t9*\x17\xad\xc1\x1c\xa5\x98'):
    return hashlib.sha1((value + s).encode('utf-8')).hexdigest()


def mksecret(length):
    return ''.join(random.choice(ascii_letters + digits) for x in range(length))


class Bloomfilter:
    """A space-efficient probabilistic data structure. False-positive rate:

        * 1e-05 for  <80 elements
        * 1e-04 for <105 elements
        * 1e-03 for <142 elements

    Uses a 256 byte array (2048 bits) and 11 hash functions. 256 byte because
    of space efficiency (array is saved for each comment) and 11 hash functions
    because of best overall false-positive rate in that range.

    -- via Raymond Hettinger
       http://code.activestate.com/recipes/577684-bloom-filter/
    """

    def __init__(self, array=bytearray(256), elements=0, iterable=()):
        self.array = array
        self.elements = elements
        self.k = 11
        self.m = len(array) * 8

        for item in iterable:
            self.add(item)

    def get_probes(self, key):
        h = int(hashlib.sha256(key.encode()).hexdigest(), 16)
        for _ in range(self.k):
            yield h & self.m - 1
            h >>= self.k

    def add(self, key):
        for i in self.get_probes(key):
            self.array[i//8] |= 2 ** (i%8)
        self.elements += 1

    @property
    def density(self):
        c = ''.join(format(x, '08b') for x in self.array)
        return c.count('1') / len(c)

    def __contains__(self, key):
        return all(self.array[i//8] & (2 ** (i%8)) for i in self.get_probes(key))

    def __len__(self):
        return self.elements
