
from __future__ import print_function, unicode_literals

from itertools import chain


from urllib.parse import unquote

import html5lib


def thread(data, default=u"Untitled.", id=None):
    """
    Extract <h1> title from web page. The title is *probably* the text node,
    which is the nearest H1 node in context to an element with the `isso-thread` id.
    """

    html = html5lib.parse(data, treebuilder="dom")

    assert html.lastChild.nodeName == "html"
    html = html.lastChild

    # aka getElementById, but limited to div and section tags
    el = list(filter(lambda i: i.attributes["id"].value == "isso-thread",
                     filter(lambda i: "id" in i.attributes,
                            chain(*map(html.getElementsByTagName, ("div", "section"))))))

    if not el:
        return id, default

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

    try:
        id = unquote(el.attributes["data-isso-id"].value)
    except (KeyError, AttributeError):
        pass

    try:
        return id, unquote(el.attributes["data-title"].value)
    except (KeyError, AttributeError):
        pass

    while el is not None:  # el.parentNode is None in the very end

        visited.append(el)
        rv = recurse(el)

        if rv:
            return id, ''.join(gettext(rv)).strip()

        el = el.parentNode

    return id, default
