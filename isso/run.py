# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import os

from isso import make_app
from isso import dist, config

application = make_app(
    config.load(
        os.path.join(dist.location, dist.project_name, "defaults.ini"),
        os.environ.get('ISSO_SETTINGS')),
    multiprocessing=True)
