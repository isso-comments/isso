# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

from __future__ import division

import json

import socket
import httplib

import math
import random
import hashlib
import contextlib

from string import ascii_letters, digits
from urlparse import urlparse

from isso.models import Comment


class IssoEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Comment):
            return dict((field, value) for field, value in obj.iteritems())

        return json.JSONEncoder.default(self, obj)


def urlexists(host, path):
    with contextlib.closing(httplib.HTTPConnection(host)) as con:
        try:
            con.request('HEAD', path)
        except socket.error:
            return False
        return con.getresponse().status == 200


def normalize(host):
    """Make `host` compatible with :py:mod:`httplib`."""

    if not host.startswith(('http://', 'https://')):
        host = 'http://' + host
    rv = urlparse(host)
    return (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc


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

