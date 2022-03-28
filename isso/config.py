# -*- encoding: utf-8 -*-

import datetime
import logging
import pkg_resources
import re

from email.utils import parseaddr, formataddr
from configparser import ConfigParser, NoOptionError, NoSectionError, DuplicateSectionError

logger = logging.getLogger("isso")

default_config_file = pkg_resources.resource_filename('isso', 'isso.cfg')


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
    regex = "".join(["((?P<%s>\\d+)%s ?)?" % (k, k[0]) for k in keys])
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

        * Parse human-readable timedelta such as "15m" as "15 minutes"
        * Handle indented lines as "lists"
        * Disable string interpolation ('%s') for values
    """

    def __init__(self, *args, **kwargs):
        """Supply modified defaults to configparser.ConfigParser
        https://docs.python.org/3.9/library/configparser.html#configparser.ConfigParser
        allow_no_value=True: Allow empty config keys
        interpolation=None:  Do not attempt to use python string interpolation on
                             values. This is especially important for parsing
                             passwords that might contain '%'
        """
        return super(IssoParser, self).__init__(
            allow_no_value=True, interpolation=None, *args, **kwargs)

    def getint(self, section, key):
        try:
            delta = timedelta(self.get(section, key))
        except ValueError:
            return super(IssoParser, self).getint(section, key)
        else:
            try:
                return int(delta.total_seconds())
            except AttributeError:
                return int(delta.total_seconds())

    def getlist(self, section, key):
        return list(map(str.strip, self.get(section, key).split(',')))

    def getiter(self, section, key):
        for item in map(str.strip, self.get(section, key).split('\n')):
            if item:
                yield item

    def section(self, section):
        return Section(self, section)


def default_file():
    return default_config_file


def new(options=None):

    cp = IssoParser()

    if options:
        cp.read_dict(options)

    return cp


def load(default, user=None):

    # return set of (section, option)
    def setify(cp):
        return set((section, option) for section in cp.sections()
                   for option in cp.options(section))

    parser = new()
    with open(default, 'r') as f:
        parser.read_file(f)

    a = setify(parser)

    if user:
        with open(user, 'r') as f:
            parser.read_file(f)

    for item in setify(parser).difference(a):
        logger.warning("no such option: [%s] %s", *item)
        if item in (("server", "host"), ("server", "port")):
            logger.warning("use `listen = http://$host:$port` instead")
        if item == ("smtp", "ssl"):
            logger.warning("use `security = none | starttls | ssl` instead")
        if item == ("general", "session-key"):
            logger.info("Your `session-key` has been stored in the "
                        "database itself, this option is now unused")

    try:
        parser.add_section('smtp')
    except DuplicateSectionError:
        pass
    try:
        fromaddr = parser.get("smtp", "from")
    except (NoOptionError, NoSectionError):
        fromaddr = ''
    if not parseaddr(fromaddr)[0]:
        parser.set("smtp", "from",
                   formataddr(("Ich schrei sonst!", fromaddr)))

    return parser
