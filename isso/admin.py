
from werkzeug.wrappers import Response


def index(app, environ, request):
    return Response('', 200)
