# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os
import pkg_resources

from isso import make_app
from isso import dist, config

application = make_app(
    config.load(
        pkg_resources.resource_filename('isso', 'defaults.ini'),
        os.environ.get('ISSO_SETTINGS')),
    multiprocessing=True)
