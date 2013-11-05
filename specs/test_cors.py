
from __future__ import unicode_literals

from werkzeug.test import Client
from werkzeug.wrappers import Response

from isso.wsgi import CORSMiddleware


def hello_world(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ["Hello, World."]


def test_simple_CORS():

    app = CORSMiddleware(hello_world, hosts=[
        "https://example.tld/",
        "http://example.tld/",
        "http://example.tld",
    ])

    client = Client(app, Response)

    rv = client.get("/", headers={"ORIGIN": "https://example.tld"})

    assert rv.headers["Access-Control-Allow-Origin"] == "https://example.tld"
    assert rv.headers["Access-Control-Allow-Headers"] == "Origin, Content-Type"
    assert rv.headers["Access-Control-Allow-Credentials"] == "true"
    assert rv.headers["Access-Control-Allow-Methods"] == "GET, POST, PUT, DELETE"
    assert rv.headers["Access-Control-Expose-Headers"] == "X-Set-Cookie"

    a = client.get("/", headers={"ORIGIN": "http://example.tld/"})
    assert a.headers["Access-Control-Allow-Origin"] == "http://example.tld"

    b = client.get("/", headers={"ORIGIN": "http://example.tld"})
    assert a.headers["Access-Control-Allow-Origin"] == "http://example.tld"

    c = client.get("/", headers={"ORIGIN": "http://foo.other/"})
    assert a.headers["Access-Control-Allow-Origin"] == "http://example.tld"


def test_preflight_CORS():

    app = CORSMiddleware(hello_world, hosts=["http://example.tld"])
    client = Client(app, Response)

    rv = client.open(method="OPTIONS", path="/", headers={"ORIGIN": "http://example.tld"})
    assert rv.status_code == 200

    for hdr in ("Origin", "Headers", "Credentials", "Methods"):
        assert "Access-Control-Allow-%s" % hdr in rv.headers

    assert rv.headers["Access-Control-Allow-Origin"] == "http://example.tld"
