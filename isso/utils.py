# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import json
import socket
import httplib
import contextlib

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


def determine(host):
    """Make `host` compatible with :py:mod:`httplib`."""

    if not host.startswith(('http://', 'https://')):
        host = 'http://' + host
    rv = urlparse(host)
    return (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc


def import_object(name):
    if '.' not in name:
        return __import__(name)

    parts = name.split('.')
    obj = __import__('.'.join(parts[:-1]), None, None, [parts[-1]], 0)
    return getattr(obj, parts[-1])
