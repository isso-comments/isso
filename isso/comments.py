
from werkzeug.wrappers import Response
from werkzeug.exceptions import abort


def comment(app, environ, request, path, id=None):
    return Response('', 200)
