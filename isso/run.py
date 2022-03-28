# -*- encoding: utf-8 -*-

import os
import sys

from isso import config, make_app

# Mock make_app because it is run by pytest
# with the --doctest-modules flag
# which will fail because make_app will exit
# without valid configuration
# https://stackoverflow.com/a/44595269/1279355
if "pytest" in sys.modules:
    make_app = lambda config, multiprocessing: True # noqa

application = make_app(
    config.load(
        config.default_file(),
        os.environ.get('ISSO_SETTINGS')),
    multiprocessing=True)
