
import os
import logging

try:
    from urlparse import urlparse
except ImportError:
    from urllib.parse import urlparse

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

        if "HTTP_ORIGIN" in environ:
            origin = environ["HTTP_ORIGIN"]
        elif "HTTP_REFERER" in environ:
            rv = urlparse(environ["HTTP_REFERER"])
            origin = rv.scheme + "://" + rv.hostname + (":" + str(rv.port) if rv.port else "")
        else:
            origin = wsgi.host(environ)

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
