# -*- encoding: utf-8 -*-

class SubURI(object):

    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):

        script_name = environ.get('HTTP_X_SCRIPT_NAME')
        if script_name:
            environ['SCRIPT_NAME'] = script_name
            path_info = environ['PATH_INFO']
            if path_info.startswith(script_name):
                environ['PATH_INFO'] = path_info[len(script_name):]

        return self.app(environ, start_response)


class CORSMiddleWare(object):

    def __init__(self, app, hosts):
        self.app = app
        self.hosts = hosts

    def __call__(self, environ, start_response):

        def add_cors_headers(status, headers, exc_info=None):

            for host in self.hosts:
                if environ.get("HTTP_ORIGIN", None) == host.rstrip("/"):
                    origin = host.rstrip("/")
                    break
            else:
                origin = host.rstrip("/")

            headers.append(("Access-Control-Allow-Origin", origin.encode("latin-1")))
            headers.append(("Access-Control-Allow-Headers", "Origin, Content-Type"))
            headers.append(("Access-Control-Allow-Credentials", "true"))
            headers.append(("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE"))
            return start_response(status, headers, exc_info)

        if environ.get("REQUEST_METHOD") == "OPTIONS":
            add_cors_headers("200 Ok", [("Content-Type", "text/plain")])
            return ['200 Ok']

        return self.app(environ, add_cors_headers)
