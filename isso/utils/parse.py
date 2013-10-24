
from __future__ import print_function

import re
import datetime

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse


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

    >>> print(host("http://example.tld/"))
    ('example.tld', 80)
    >>> print(host("https://example.tld/"))
    ('example.tld', 443)
    >>> print(host("example.tld"))
    ('example.tld', 80)
    >>> print(host("example.tld:42"))
    ('example.tld', 42)
    """

    if not name.startswith(('http://', 'https://')):
        name = 'http://' + name

    rv = urlparse(name)
    if rv.scheme == 'https':
        return (rv.netloc, 443)
    return (rv.netloc.rsplit(':')[0], rv.port or 80)
