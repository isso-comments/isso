# -*- encoding: utf-8 -*-

try:
    text_type = unicode  # Python 2
    string_types = (str, unicode)
    PY2K = True
except NameError:        # Python 3
    PY2K = False
    text_type = str
    string_types = (str, )

try:
    buffer = memoryview  # Python 2.7 and Python 3
except NameError:
    buffer = buffer      # Python 2.6

if not PY2K:
    # buffer = memoryview  # noqa: F821 undefined name 'memoryview' in Python 2.6
    filter, map, zip = filter, map, zip
    iteritems = lambda dikt: iter(dikt.items())  # noqa: E731
    from functools import reduce
else:
    # buffer = buffer
    from itertools import ifilter, imap, izip
    filter, map, zip = ifilter, imap, izip
    iteritems = lambda dikt: dikt.iteritems()   # noqa: E731
    reduce = reduce
