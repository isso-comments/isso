# -*- encoding: utf-8 -*-

import socket

from contextlib import closing

try:
    import httplib
except ImportError:
    import http.client as httplib

import html5lib

from isso.utils import parse


def urlexists(host, path):

    host, port = parse.host(host)
    http = httplib.HTTPSConnection if port == 443 else httplib.HTTPConnection

    with closing(http(host, port, timeout=3)) as con:
        try:
            con.request('HEAD', path)
        except (httplib.HTTPException, socket.error):
            return False
        return con.getresponse().status == 200


def heading(host, path):
    """Connect to `host`, GET path and start from #isso-thread to search for
    a possible heading (h1). Returns `None` if nothing found."""

    host, port = parse.host(host)
    http = httplib.HTTPSConnection if port == 443 else httplib.HTTPConnection

    with closing(http(host, port, timeout=15)) as con:
        con.request('GET', path)
        html = html5lib.parse(con.getresponse().read(), treebuilder="dom")

    assert html.lastChild.nodeName == "html"
    html = html.lastChild

    # aka getElementById
    el = list(filter(lambda i: i.attributes["id"].value == "isso-thread",
              filter(lambda i: i.attributes.has_key("id"), html.getElementsByTagName("div"))))

    if not el:
        return "Untitled"

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

    return "Untitled."

