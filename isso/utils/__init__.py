# -*- encoding: utf-8 -*-

from __future__ import division

import pkg_resources
werkzeug = pkg_resources.get_distribution("werkzeug")

import json
import hashlib

from werkzeug.wrappers import Request
from werkzeug.exceptions import BadRequest

try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress

import misaka


def anonymize(remote_addr):
    """
    Anonymize IPv4 and IPv6 :param remote_addr: to /24 (zero'd)
    and /48 (zero'd).

    >>> anonymize(u'12.34.56.78')  # doctest: +IGNORE_UNICODE
    '12.34.56.0'
    >>> anonymize(u'1234:5678:90ab:cdef:fedc:ba09:8765:4321') # doctest: +IGNORE_UNICODE
    '1234:5678:90ab:0000:0000:0000:0000:0000'
    >>> anonymize(u'::ffff:127.0.0.1')  # doctest: +IGNORE_UNICODE
    '127.0.0.0'
    """
    try:
        ipv4 = ipaddress.IPv4Address(remote_addr)
        return u''.join(ipv4.exploded.rsplit('.', 1)[0]) + '.' + '0'
    except ipaddress.AddressValueError:
        ipv6 = ipaddress.IPv6Address(remote_addr)
        if ipv6.ipv4_mapped is not None:
            return anonymize(ipv6.ipv4_mapped)
        return u'' + ipv6.exploded.rsplit(':', 5)[0] + ':' + ':'.join(['0000']*5)


class Bloomfilter:
    """A space-efficient probabilistic data structure. False-positive rate:

        * 1e-05 for  <80 elements
        * 1e-04 for <105 elements
        * 1e-03 for <142 elements

    Uses a 256 byte array (2048 bits) and 11 hash functions. 256 byte because
    of space efficiency (array is saved for each comment) and 11 hash functions
    because of best overall false-positive rate in that range.

    >>> bf = Bloomfilter()
    >>> bf.add("127.0.0.1")
    >>> not any(map(bf.__contains__, ("1.2.%i.4" for i in range(256))))
    True

    >>> bf = Bloomfilter()
    >>> for i in range(256):
    ...     bf.add("1.2.%i.4" % i)
    ...
    >>> len(bf)
    256
    >>> "1.2.3.4" in bf
    True
    >>> "127.0.0.1" in bf
    False

    -- via Raymond Hettinger
       http://code.activestate.com/recipes/577684-bloom-filter/
    """

    def __init__(self, array=None, elements=0, iterable=()):
        self.array = array or bytearray(256)
        self.elements = elements
        self.k = 11
        self.m = len(self.array) * 8

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


def markdown(text):
    return misaka.html(text, extensions= misaka.EXT_STRIKETHROUGH
        | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK
        | misaka.HTML_SKIP_HTML  | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)


def origin(hosts):

    hosts = [x.rstrip("/") for x in hosts]

    def func(environ):
        for host in hosts:
            if environ.get("HTTP_ORIGIN", None) == host:
                return host
        else:
            return hosts[0]

    return func
