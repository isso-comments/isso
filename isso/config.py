# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import re
import logging
import datetime

from email.utils import parseaddr, formataddr
try:
    from backports.configparser import ConfigParser
except ImportError:
    from configparser import ConfigParser

from isso.compat import text_type as str

logger = logging.getLogger("isso")


# Python 2.6 compatibility
def total_seconds(td):
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


def timedelta(string):
    """
    Parse :param string: into :class:`datetime.timedelta`, you can use any
    (logical) combination of Nw, Nd, Nh and Nm, e.g. `1h30m` for 1 hour, 30
    minutes or `3w` for 3 weeks.

    Raises a ValueError if the input is invalid/unparseable.

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
    for k, v in re.match(regex, string).groupdict(default="0").items():
        kwargs[k] = int(v)

    rv = datetime.timedelta(**kwargs)
    if rv == datetime.timedelta():
        raise ValueError("invalid human-readable timedelta")

    return datetime.timedelta(**kwargs)


class Section(object):
    """A wrapper around :class:`IssoParser` that returns a partial configuration
    section object.

    >>> conf = new({"foo": {"bar": "spam"}})
    >>> section = conf.section("foo")
    >>> conf.get("foo", "bar") == section.get("bar")
    True
    """

    def __init__(self, conf, section):
        self.conf = conf
        self.section = section

    def get(self, key):
        return self.conf.get(self.section, key)

    def getint(self, key):
        return self.conf.getint(self.section, key)

    def getlist(self, key):
        return self.conf.getlist(self.section, key)

    def getiter(self, key):
        return self.conf.getiter(self.section, key)

    def getboolean(self, key):
        return self.conf.getboolean(self.section, key)


class IssoParser(ConfigParser):
    """Parse INI-style configuration with some modifications for Isso.

        * parse human-readable timedelta such as "15m" as "15 minutes"
        * handle indented lines as "lists"
    """

    def getint(self, section, key):
        try:
            delta = timedelta(self.get(section, key))
        except ValueError:
            return super(IssoParser, self).getint(section, key)
        else:
            try:
                return int(delta.total_seconds())
            except AttributeError:
                return int(total_seconds(delta))

    def getlist(self, section, key):
        return list(map(str.strip, self.get(section, key).split(',')))

    def getiter(self, section, key):
        for item in map(str.strip, self.get(section, key).split('\n')):
            if item:
                yield item

    def section(self, section):
        return Section(self, section)


def new(options=None):

    cp = IssoParser(allow_no_value=True)

    if options:
        cp.read_dict(options)

    return cp


def load(default, user=None):

    # return set of (section, option)
    setify = lambda cp: set((section, option) for section in cp.sections()
                            for option in cp.options(section))

    parser = new()
    parser.read(default)

    a = setify(parser)

    if user:
        parser.read(user)

    for item in setify(parser).difference(a):
        logger.warn("no such option: [%s] %s", *item)
        if item in (("server", "host"), ("server", "port")):
            logger.warn("use `listen = http://$host:$port` instead")
        if item == ("smtp", "ssl"):
            logger.warn("use `security = none | starttls | ssl` instead")
        if item == ("general", "session-key"):
            logger.info("Your `session-key` has been stored in the "
                        "database itself, this option is now unused")

    from_address = parser.get("smtp", "from").strip()

    if from_address != '' and parseaddr(from_address) == (None, None):
        if '@' not in from_address:
            logger.warn("Your `from` address doesn't contain an @ sign. "
                        "It is reset to an empty address.")
            parser.set("smtp", "from", "")

        elif ' ' in from_address:
            logger.warn("Your `from` address contains a space. "
                        "It is reset to an empty address.")
            parser.set("smtp", "from", "")

        else:
            parser.set("smtp", "from",
                formataddr(("Ich schrei sonst!", from_address)))

    return parser
