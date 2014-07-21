# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import json

from werkzeug.wrappers import Response

from isso import local
from isso.compat import text_type as str


class Info(object):

    def __init__(self, conf):
        self.moderation = conf.getboolean("moderation", "enabled")

    def show(self, environ, request):

        rv = {
            "version": dist.version,
            "host": str(local("host")),
            "origin": str(local("origin")),
            "moderation": self.moderation,
            }

        return Response(json.dumps(rv), 200, content_type="application/json")
