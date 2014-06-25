# -*- encoding: utf-8 -*-

import os

from isso import make_app
from isso import dist, config

application = make_app(
    config.load(
        os.path.join(dist.location, "isso", "defaults.ini"),
        os.environ.get('ISSO_SETTINGS')),
    multiprocessing=True)
