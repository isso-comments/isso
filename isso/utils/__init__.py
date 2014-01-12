# -*- encoding: utf-8 -*-

from __future__ import division

import pkg_resources
werkzeug = pkg_resources.get_distribution("werkzeug")

import io
import json
import random
import hashlib

from string import ascii_letters, digits

try:
    from html.parser import HTMLParser, HTMLParseError
except ImportError:
    from HTMLParser import HTMLParser, HTMLParseError

from werkzeug.utils import escape
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


class Sanitizer(HTMLParser, object):
    """Sanitize HTML output: remove unsafe HTML tags such as iframe or
    script based on a whitelist of allowed tags."""

    safe = set([
        "p", "a", "pre", "blockquote",
        "h1", "h2", "h3", "h4", "h5", "h6",
        "em", "sub", "sup", "del", "ins", "math",
        "dl", "ol", "ul", "li"])

    @classmethod
    def format(cls, attrs):
        res = []
        for key, value in attrs:
            if value is None:
                res.append(key)
            else:
                res.append(u'{0}="{1}"'.format(key, escape(value)))
        return ' '.join(res)

    def __init__(self, html):
        super(Sanitizer, self).__init__()
        self.result = io.StringIO()
        self.feed(html)
        self.result.seek(0)

    def handle_starttag(self, tag, attrs):
        if tag in Sanitizer.safe:
            self.result.write(u"<" + tag)
            if attrs:
                self.result.write(" " + Sanitizer.format(attrs))
            self.result.write(u">")

    def handle_data(self, data):
        self.result.write(data)

    def handle_endtag(self, tag):
        if tag in Sanitizer.safe:
            self.result.write(u"</" + tag + ">")

    def handle_startendtag(self, tag, attrs):
        if tag in Sanitizer.safe:
            self.result.write(u"<" + tag)
            if attrs:
                self.result.write(" " + Sanitizer.format(attrs))
            self.result.write(u"/>")

    def handle_entityref(self, name):
        self.result.write(u'&' + name + ';')

    def handle_charref(self, char):
        self.result.write(u'&#' + char + ';')


def markdown(text):
    """Convert Markdown to (safe) HTML.

    >>> markdown("*Ohai!*") # doctest: +IGNORE_UNICODE
    '<p><em>Ohai!</em></p>'
    >>> markdown("<em>Hi</em>") # doctest: +IGNORE_UNICODE
    '<p><em>Hi</em></p>'
    >>> markdown("<script>alert('Onoe')</script>") # doctest: +IGNORE_UNICODE
    "<p>alert('Onoe')</p>"
    >>> markdown("http://example.org/ and sms:+1234567890") # doctest: +IGNORE_UNICODE
    '<p><a href="http://example.org/">http://example.org/</a> and sms:+1234567890</p>'
    """

    # ~~strike through~~, sub script: 2^(nd) and http://example.org/ auto-link
    exts = misaka.EXT_STRIKETHROUGH | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK

    # remove HTML tags, skip <img> (for now) and only render "safe" protocols
    html = misaka.HTML_SKIP_STYLE | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK

    rv = misaka.html(text, extensions=exts, render_flags=html).rstrip("\n")
    if not rv.startswith("<p>") and not rv.endswith("</p>"):
        rv = "<p>" + rv + "</p>"

    return Sanitizer(rv).result.read()


def origin(hosts):

    hosts = [x.rstrip("/") for x in hosts]

    def func(environ):
        for host in hosts:
            if environ.get("HTTP_ORIGIN", None) == host:
                return host
        else:
            return hosts[0]

    return func
