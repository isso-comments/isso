# -*- encoding: utf-8 -*-

from werkzeug.exceptions import BadRequest


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
