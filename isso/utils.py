# -*- encoding: utf-8 -*-
#
# Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
# License: BSD Style, 2 clauses. see isso/__init__.py

import json
import socket
import httplib
import urlparse
import contextlib

import misaka
import werkzeug.routing

from isso.models import Comment


class IssoEncoder(json.JSONEncoder):

    def default(self, obj):
        if isinstance(obj, Comment):
            return dict((field, value) for field, value in obj.iteritems())

        return json.JSONEncoder.default(self, obj)


class RegexConverter(werkzeug.routing.BaseConverter):
    def __init__(self, url_map, *items):
        super(RegexConverter, self).__init__(url_map)
        self.regex = items[0]


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
    rv = urlparse.urlparse(host)
    return (rv.netloc + ':443') if rv.scheme == 'https' else rv.netloc


def markdown(text):
    return misaka.html(text,
        extensions = misaka.EXT_STRIKETHROUGH | misaka.EXT_SUPERSCRIPT | misaka.EXT_AUTOLINK \
                   | misaka.HTML_SKIP_HTML | misaka.HTML_SKIP_IMAGES | misaka.HTML_SAFELINK)
