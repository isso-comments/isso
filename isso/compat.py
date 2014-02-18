# -*- encoding: utf-8 -*-

import sys
PY2K = sys.version_info[0] == 2

if not PY2K:

    map, zip, filter = map, zip, filter
    from functools import reduce

    text_type = str
    string_types = (str, )

    buffer = memoryview
else:

    from itertools import imap, izip, ifilter
    map, zip, filter = imap, izip, ifilter
    reduce = reduce

    text_type = unicode
    string_types = (str, unicode)

    buffer = buffer
