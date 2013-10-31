
from __future__ import print_function

import re
import datetime

from itertools import chain

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

import html5lib

from isso.compat import map, filter, PY2K

if PY2K:  # http://bugs.python.org/issue12984
    from xml.dom.minidom import NamedNodeMap
    NamedNodeMap.__contains__ = lambda self, key: self.has_key(key)


def timedelta(value):
    """
    Parse :param value: into :class:`datetime.timedelta`, you can use any (logical)
    combination of Nw, Nd, Nh and Nm, e.g. `1h30m` for 1 hour, 30 minutes or `3w` for
    3 weeks. Raises a ValueError if the input is invalid/unparseable.

    >>> print(timedelta("3w"))
    21 days, 0:00:00
    >>> print(timedelta("3w 12h 57m"))
    21 days, 12:57:00
    >>> print(timedelta("1h30m37s"))
    1:30:37
    >>> print(timedelta("1asdf3w"))
    Traceback (most recent call last):
        ...
    ValueError: invalid human-readable timedelta
    """

    keys = ["weeks", "days", "hours", "minutes", "seconds"]
    regex = "".join(["((?P<%s>\d+)%s ?)?" % (k, k[0]) for k in keys])
    kwargs = {}
    for k, v in re.match(regex, value).groupdict(default="0").items():
        kwargs[k] = int(v)

    rv = datetime.timedelta(**kwargs)
    if rv == datetime.timedelta():
        raise ValueError("invalid human-readable timedelta")
    return datetime.timedelta(**kwargs)


def host(name):
    """
    Parse :param name: into `httplib`-compatible host:port.

    >>> host("http://example.tld/")
    ('example.tld', 80, False)
    >>> host("https://example.tld/")
    ('example.tld', 443, True)
    >>> host("example.tld")
    ('example.tld', 80, False)
    >>> host("example.tld:42")
    ('example.tld', 42, False)
    >>> host("https://example.tld:80/")
    ('example.tld', 80, True)
    """

    if not name.startswith(('http://', 'https://')):
        name = 'http://' + name

    rv = urlparse(name)
    if rv.scheme == 'https' and rv.port is None:
        return (rv.netloc, 443, True)
    return (rv.netloc.rsplit(':')[0], rv.port or 80, rv.scheme == 'https')


def title(data, default=u"Untitled."):
    """
    Extract <h1> title from web page. The title is *probably* the text node,
    which is the nearest H1 node in context to an element with the `isso-thread` id.

    >>> title("asdf")  # doctest: +IGNORE_UNICODE
    u'Untitled.'
    >>> title('''
    ... <html>
    ... <head>
    ...     <title>Foo!</title>
    ... </head>
    ... <body>
    ...     <header>
    ...         <h1>generic website title.</h1>
    ...         <h2>subtile title.</h2>
    ...     </header>
    ...     <article>
    ...         <header>
    ...             <h1>Can you find me?</h1>
    ...         </header>
    ...         <section id="isso-thread">
    ...         </section>
    ...     </article>
    ... </body>
    ... </html>''')  # doctest: +IGNORE_UNICODE
    u'Can you find me?'
    """

    html = html5lib.parse(data, treebuilder="dom")

    assert html.lastChild.nodeName == "html"
    html = html.lastChild

    # aka getElementById, but limited to div and section tags
    el = list(filter(lambda i: i.attributes["id"].value == "isso-thread",
              filter(lambda i: "id" in i.attributes,
                     chain(*map(html.getElementsByTagName, ("div", "section"))))))

    if not el:
        return default

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

    return default
