# -*- encoding: utf-8 -*-

from __future__ import division

import pkg_resources
werkzeug = pkg_resources.get_distribution("werkzeug")

import json
import random
import hashlib

from string import ascii_letters, digits

from werkzeug.wrappers import Request
from werkzeug.exceptions import BadRequest

try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress


def anonymize(remote_addr):
    """
    Anonymize IPv4 and IPv6 :param remote_addr: to /24 (zero'd)
    and /48 (zero'd).

    >>> anonymize(u'12.34.56.78')  # doctest: +IGNORE_UNICODE
    '12.34.56.0'
    >>> anonymize(u'1234:5678:90ab:cdef:fedc:ba09:8765:4321') # doctest: +IGNORE_UNICODE
    '1234:5678:90ab:0000:0000:0000:0000:0000'
    """
    try:
        ipv4 = ipaddress.IPv4Address(remote_addr)
        return u''.join(ipv4.exploded.rsplit('.', 1)[0]) + '.' + '0'
    except ipaddress.AddressValueError:
        ipv6 = ipaddress.IPv6Address(remote_addr)
        if ipv6.ipv4_mapped is not None:
            return anonymize(ipv6.ipv4_mapped)
        return u'' + ipv6.exploded.rsplit(':', 5)[0] + ':' + ':'.join(['0000']*5)


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


class JSONRequest(Request):

    if werkzeug.version.startswith("0.8"):
        def get_data(self, **kw):
            return self.data.decode('utf-8')

    def get_json(self):
        try:
            return json.loads(self.get_data(as_text=True))
        except ValueError:
            raise BadRequest('Unable to read JSON request')
