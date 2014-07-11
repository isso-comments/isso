# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os

from isso import make_app
from isso.core import Config

application = make_app(Config.load(os.environ.get('ISSO_SETTINGS')),
                       multiprocessing=True)
