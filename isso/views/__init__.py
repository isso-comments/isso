# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import json

from werkzeug.wrappers import Response
from werkzeug.routing import Rule
from werkzeug.exceptions import BadRequest

from isso import local
from isso.compat import text_type as str


class requires:
    """Verify that the request URL contains and can parse the parameter.

    .. code-block:: python

        @requires(int, "id")
        def view(..., id):
            assert isinstance(id, int)

    Returns a 400 Bad Request that contains a specific error message.
    """

    def __init__(self, type, param):
        self.param = param
        self.type = type

    def __call__(self, func):
        def dec(cls, env, req, *args, **kwargs):

            if self.param not in req.args:
                raise BadRequest("missing %s query" % self.param)

            try:
                kwargs[self.param] = self.type(req.args[self.param])
            except TypeError:
                raise BadRequest("invalid type for %s, expected %s" % (self.param, self.type))

            return func(cls, env, req, *args, **kwargs)

        return dec


class Info(object):

    def __init__(self, isso):
        self.moderation = isso.conf.getboolean("moderation", "enabled")
        self.users = list(map(lambda line: str.strip(line.split(',')[0]),
            isso.conf.getiter("user", "accounts")))
        isso.urls.add(Rule('/info', endpoint=self.show))

    def show(self, environ, request):

        rv = {
            "version": dist.version,
            "host": str(local("host")),
            "origin": str(local("origin")),
            "moderation": self.moderation,
            "users": self.users
        }

        return Response(json.dumps(rv), 200, content_type="application/json")
