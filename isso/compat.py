# -*- encoding: utf-8 -*-

import sys
PY2K = sys.version_info[0] == 2

if not PY2K:
    # iterkeys = lambda d: iter(d.keys())
    # iteritems = lambda d: iter(d.items())

    text_type = str
    string_types = (str, )

    buffer = memoryview
else:
    # iterkeys = lambda d: d.iterkeys()
    # iteritems = lambda d: d.iteritems()

    text_type = unicode
    string_types = (str, unicode)

    buffer = buffer
