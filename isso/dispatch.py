# -*- encoding: utf-8 -*-

from glob import glob
import os
import logging

from werkzeug.wsgi import DispatcherMiddleware
from werkzeug.wrappers import Response

from isso import make_app, wsgi
from isso.core import Config

logger = logging.getLogger("isso")


class Dispatcher(DispatcherMiddleware):
    """
    A dispatcher to support different websites. Dispatches based on
    a relative URI, e.g. /foo.example and /other.bar.
    """

    def __init__(self, *confs):

        self.isso = {}

        for i, conf in enumerate(map(Config.load, confs)):

            if not conf.get("general", "name"):
                logger.warn("unable to dispatch %r, no 'name' set", confs[i])
                continue

            self.isso["/" + conf.get("general", "name")] = make_app(conf)

        super(Dispatcher, self).__init__(self.default, mounts=self.isso)

    def __call__(self, environ, start_response):

        # clear X-Script-Name as the PATH_INFO is already adjusted
        environ.pop('HTTP_X_SCRIPT_NAME', None)

        return super(Dispatcher, self).__call__(environ, start_response)

    def default(self, environ, start_response):
        resp = Response("\n".join(self.isso.keys()), 404, content_type="text/plain")
        return resp(environ, start_response)


if "ISSO_SETTINGS" in os.environ:
    confs = os.environ["ISSO_SETTINGS"].split(";")
    for path in confs:
        if not os.path.isfile(path):
            logger.fatal("%s: no such file", path)
            break
    else:
        application = wsgi.SubURI(Dispatcher(*confs))

elif "ISSO_SETTINGS_DIR" in os.environ:
    conf_glob = os.path.join(os.environ["ISSO_SETTINGS_DIR"], '*.cfg')
    confs = glob(conf_glob)
    application = wsgi.SubURI(Dispatcher(*confs))

else:
    logger.fatal('environment variable ISSO_SETTINGS or ISSO_SETTINGS_DIR must be set')
