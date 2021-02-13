# -*- encoding: utf-8 -*-

from __future__ import division, unicode_literals

import pkg_resources
werkzeug = pkg_resources.get_distribution("werkzeug")

import hashlib
import json
import os

from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest

from isso.wsgi import Request

try:
    import ipaddress
except ImportError:
    import ipaddr as ipaddress


def anonymize(remote_addr):
    """
    Anonymize IPv4 and IPv6 :param remote_addr: to /24 (zero'd)
    and /48 (zero'd).

    """
    if not isinstance(remote_addr, str) and isinstance(remote_addr, str):
        remote_addr = remote_addr.decode('ascii', 'ignore')
    try:
        ipv4 = ipaddress.IPv4Address(remote_addr)
        return u''.join(ipv4.exploded.rsplit('.', 1)[0]) + '.' + '0'
    except ipaddress.AddressValueError:
        try:
            ipv6 = ipaddress.IPv6Address(remote_addr)
            if ipv6.ipv4_mapped is not None:
                return anonymize(str(ipv6.ipv4_mapped))
            return u'' + ipv6.exploded.rsplit(':', 5)[0] + ':' + ':'.join(['0000'] * 5)
        except ipaddress.AddressValueError:
            return u'0.0.0.0'


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
            self.array[i // 8] |= 2 ** (i % 8)
        self.elements += 1

    def __contains__(self, key):
        return all(self.array[i // 8] & (2 ** (i % 8)) for i in self.get_probes(key))

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


def render_template(template_name, **context):
    template_path = os.path.join(os.path.dirname(__file__),
                                 '..', 'templates')
    jinja_env = Environment(loader=FileSystemLoader(template_path),
                            autoescape=True)

    def datetimeformat(value):
        return datetime.fromtimestamp(value).strftime('%H:%M / %d-%m-%Y')

    jinja_env.filters['datetimeformat'] = datetimeformat
    t = jinja_env.get_template(template_name)
    return Response(t.render(context), mimetype='text/html')


class JSONResponse(Response):

    def __init__(self, obj, *args, **kwargs):
        kwargs["content_type"] = "application/json"
        super(JSONResponse, self).__init__(
            json.dumps(obj).encode("utf-8"), *args, **kwargs)


class XMLResponse(Response):
    def __init__(self, obj, *args, **kwargs):
        kwargs["content_type"] = "text/xml"
        super(XMLResponse, self).__init__(
            obj, *args, **kwargs)
