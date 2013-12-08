
import os
import logging

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

from werkzeug.wrappers import Request
from werkzeug.exceptions import ImATeapot

from isso import make_app, wsgi
from isso.core import Config

logger = logging.getLogger("isso")


class Dispatcher(object):
    """
    A dispatcher to support different websites. Dispatches based on
    HTTP-Host. If HTTP-Host is not provided, display an error message.
    """

    def __init__(self, *confs):

        self.isso = {}

        for conf in map(Config.load, confs):

            app = make_app(conf)

            for origin in conf.getiter("general", "host"):
                self.isso[origin.rstrip("/")] = app

    def __call__(self, environ, start_response):

        if Request(environ).url.endswith((".js", ".css")):
            return self.isso.values()[0](environ, start_response)

        if "HTTP_X_ORIGIN" in environ and "HTTP_ORIGIN" not in environ:
            environ["HTTP_ORIGIN"] = environ["HTTP_X_ORIGIN"]

        origin = environ.get("HTTP_ORIGIN", wsgi.host(environ))

        try:
            # logger.info("dispatch %s", origin)
            return self.isso[origin](environ, start_response)
        except KeyError:
            # logger.info("unable to dispatch %s", origin)
            resp = ImATeapot("unable to dispatch %s" % origin)
            return resp(environ, start_response)


if "ISSO_SETTINGS" not in os.environ:
    logger.fatal('no such environment variable: ISSO_SETTINGS')
else:
    confs = os.environ["ISSO_SETTINGS"].split(";")
    for path in confs:
        if not os.path.isfile(path):
            logger.fatal("%s: no such file", path)
            break
    else:
        application = Dispatcher(*confs)
