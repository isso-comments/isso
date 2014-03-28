
from __future__ import print_function

import datetime
from itertools import chain

import re


try:
    from urllib import unquote
except ImportError:
    from urllib.parse import unquote

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



def thread(data, default=u"Untitled.", id=None):
    """
    Extract <h1> title from web page. The title is *probably* the text node,
    which is the nearest H1 node in context to an element with the `isso-thread` id.

    >>> thread("asdf")  # doctest: +IGNORE_UNICODE
    (None, 'Untitled.')
    >>> thread('''
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
    (None, 'Can you find me?')
    >>> thread('''
    ... <html>
    ... <body>
    ... <h1>I'm the real title!1
    ... <section data-title="No way%21" id="isso-thread">
    ... ''')  # doctest: +IGNORE_UNICODE
    (None, 'No way!')
    >>> thread('''
    ... <section id="isso-thread" data-title="Test" data-isso-id="test">
    ... ''')  # doctest: +IGNORE_UNICODE
    ('test', 'Test')
    >>> thread('''
    ... <section id="isso-thread" data-isso-id="Fuu.">
    ... ''')  # doctest: +IGNORE_UNICODE
    ('Fuu.', 'Untitled.')
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
