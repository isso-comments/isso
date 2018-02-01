# -*- encoding: utf-8 -*-

try:
    text_type = unicode  # Python 2
    string_types = (str, unicode)
    PY2K = True
except NameError:        # Python 3
    PY2K = False
    text_type = str
    string_types = (str, )

if not PY2K:
    buffer = memoryview
    filter, map, zip = filter, map, zip

    def iteritems(dikt): return iter(dikt.items())  # noqa: E731
    from functools import reduce
else:
    buffer = buffer
    from itertools import ifilter, imap, izip
    filter, map, zip = ifilter, imap, izip

    def iteritems(dikt): return dikt.iteritems()   # noqa: E731
    reduce = reduce
