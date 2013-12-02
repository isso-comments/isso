# -*- encoding: utf-8 -*-

import cgi
import json
import time
import hashlib
import functools

from itsdangerous import SignatureExpired, BadSignature

from werkzeug.http import dump_cookie
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.useragents import UserAgent

from isso.compat import text_type as str

from isso import utils, local
from isso.utils import http, parse, markdown
from isso.utils.crypto import pbkdf2
from isso.views import requires


def md5(text):
    return hashlib.md5(text.encode('utf-8')).hexdigest()


class JSON(Response):

    def __init__(self, *args):
        return super(JSON, self).__init__(*args, content_type='application/json')


def csrf(view):
    """A decorator to check if HTTP_Origin matches configured host. If not,
    return 401 Forbidden. See

       * https://www.owasp.org/index.php/Cross-Site_Request_Forgery_(CSRF)_Prevention_Cheat_Sheet#Checking_The_Origin_Header
       * http://tools.ietf.org/html/draft-abarth-origin-09
       * https://wiki.mozilla.org/Security/Origin

    for details.
    """

    def dec(self, environ, request, *args, **kwargs):

        if UserAgent(environ).browser == "msie":  # yup
            origin = request.headers.get("Referer", "")
        else:
            origin = request.headers.get("Origin", "")
        if parse.host(origin) not in map(parse.host, self.conf.getiter("host")):
            raise Forbidden("CSRF")

        return view(self, environ, request, *args, **kwargs)

    return dec


class API(object):

    FIELDS = set(['id', 'parent', 'text', 'author', 'website', 'email',
                  'mode', 'created', 'modified', 'likes', 'dislikes', 'hash'])

    # comment fields, that can be submitted
    ACCEPT = set(['text', 'author', 'website', 'email', 'parent'])

    VIEWS = [
        ('fetch',   ('GET', '/')),
        ('new',     ('POST', '/new')),
        ('count',   ('GET', '/count')),
        ('view',    ('GET', '/id/<int:id>')),
        ('edit',    ('PUT', '/id/<int:id>')),
        ('delete',  ('DELETE', '/id/<int:id>')),
        ('moderate',('GET',  '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
        ('moderate',('POST', '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
        ('like',    ('POST', '/id/<int:id>/like')),
        ('dislike', ('POST', '/id/<int:id>/dislike')),
        ('checkip', ('GET', '/check-ip'))
    ]

    def __init__(self, isso):

        self.isso = isso
        self.cache = isso.cache
        self.signal = isso.signal

        self.conf = isso.conf.section("general")
        self.moderated = isso.conf.getboolean("moderation", "enabled")

        self.guard = isso.db.guard
        self.threads = isso.db.threads
        self.comments = isso.db.comments

        for (view, (method, path)) in self.VIEWS:
            isso.urls.add(
                Rule(path, methods=[method], endpoint=getattr(self, view)))

    @classmethod
    def verify(cls, comment):

        if "text" not in comment:
            return False, "text is missing"

        if not isinstance(comment.get("parent"), (int, type(None))):
            return False, "parent must be an integer or null"

        for key in ("text", "author", "website", "email"):
            if not isinstance(comment.get(key), (str, type(None))):
                return False, "%s must be a string or null" % key

        if len(comment["text"]) < 3:
            return False, "text is too short (minimum length: 3)"

        if len(comment.get("email") or "") > 254:
            return False, "http://tools.ietf.org/html/rfc5321#section-4.5.3"

        return True, ""

    @csrf
    @requires(str, 'uri')
    def new(self, environ, request, uri):

        data = request.get_json()

        for field in set(data.keys()) - API.ACCEPT:
            data.pop(field)

        for key in ("author", "email", "website", "parent"):
            data.setdefault(key, None)

        valid, reason = API.verify(data)
        if not valid:
            return BadRequest(reason)

        for field in ("author", "email"):
            if data.get(field) is not None:
                data[field] = cgi.escape(data[field])

        data['mode'] = 2 if self.moderated else 1
        data['remote_addr'] = utils.anonymize(str(request.remote_addr))

        with self.isso.lock:
            if uri not in self.threads:
                with http.curl('GET', local("origin"), uri) as resp:
                    if resp and resp.status == 200:
                        title = parse.title(resp.read())
                    else:
                        return NotFound('URI does not exist')

                thread = self.threads.new(uri, title)
                self.signal("comments.new:new-thread", thread)
            else:
                thread = self.threads[uri]

        # notify extensions that the new comment is about to save
        self.signal("comments.new:before-save", thread, data)

        valid, reason = self.guard.validate(uri, data)
        if not valid:
            self.signal("comments.new:guard", reason)
            raise Forbidden(reason)

        with self.isso.lock:
            rv = self.comments.add(uri, data)

        # notify extension, that the new comment has been successfully saved
        self.signal("comments.new:after-save", thread, rv)

        cookie = functools.partial(dump_cookie,
            value=self.isso.sign([rv["id"], md5(rv["text"])]),
            max_age=self.conf.getint('max-age'))

        rv["text"] = markdown(rv["text"])
        rv["hash"] = str(pbkdf2(rv['email'] or rv['remote_addr'], self.isso.salt, 1000, 6))

        self.cache.set('hash', (rv['email'] or rv['remote_addr']).encode('utf-8'), rv['hash'])

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        # success!
        self.signal("comments.new:finish", thread, rv)

        resp = JSON(json.dumps(rv), 202 if rv["mode"] == 2 else 201)
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    def view(self, environ, request, id):

        rv = self.comments.get(id)
        if rv is None:
            raise NotFound

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        if request.args.get('plain', '0') == '0':
            rv['text'] = markdown(rv['text'])

        return Response(json.dumps(rv), 200, content_type='application/json')

    @csrf
    def edit(self, environ, request, id):

        try:
            rv = self.isso.unsign(request.cookies.get(str(id), ''))
        except (SignatureExpired, BadSignature):
            raise Forbidden

        if rv[0] != id:
            raise Forbidden

        # verify checksum, mallory might skip cookie deletion when he deletes a comment
        if rv[1] != md5(self.comments.get(id)["text"]):
            raise Forbidden

        data = request.get_json()

        if "text" not in data or data["text"] is None or len(data["text"]) < 3:
            raise BadRequest("no text given")

        for key in set(data.keys()) - set(["text", "author", "website"]):
            data.pop(key)

        data['modified'] = time.time()

        with self.isso.lock:
            rv = self.comments.update(id, data)

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        self.signal("comments.edit", rv)

        cookie = functools.partial(dump_cookie,
                value=self.isso.sign([rv["id"], md5(rv["text"])]),
                max_age=self.conf.getint('max-age'))

        rv["text"] = markdown(rv["text"])

        resp = JSON(json.dumps(rv), 200)
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    @csrf
    def delete(self, environ, request, id, key=None):

        try:
            rv = self.isso.unsign(request.cookies.get(str(id), ""))
        except (SignatureExpired, BadSignature):
            raise Forbidden
        else:
            if rv[0] != id:
                raise Forbidden

            # verify checksum, mallory might skip cookie deletion when he deletes a comment
            if rv[1] != md5(self.comments.get(id)["text"]):
                raise Forbidden

        item = self.comments.get(id)

        if item is None:
            raise NotFound

        self.cache.delete('hash', (item['email'] or item['remote_addr']).encode('utf-8'))

        with self.isso.lock:
            rv = self.comments.delete(id)

        if rv:
            for key in set(rv.keys()) - API.FIELDS:
                rv.pop(key)

        self.signal("comments.delete", id)

        resp = JSON(json.dumps(rv), 200)
        cookie = functools.partial(dump_cookie, expires=0, max_age=0)
        resp.headers.add("Set-Cookie", cookie(str(id)))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % id))
        return resp

    def moderate(self, environ, request, id, action, key):

        try:
            id = self.isso.unsign(key, max_age=2**32)
        except (BadSignature, SignatureExpired):
            raise Forbidden

        item = self.comments.get(id)

        if item is None:
            raise NotFound

        if request.method == "GET":
            modal = (
                "<!DOCTYPE html>"
                "<html>"
                "<head>"
                "<script>"
                "  if (confirm('%s: Are you sure?')) {"
                "      xhr = new XMLHttpRequest;"
                "      xhr.open('POST', window.location.href);"
                "      xhr.send(null);"
                "  }"
                "</script>" % action.capitalize())

            return Response(modal, 200, content_type="text/html")

        if action == "activate":
            with self.isso.lock:
                self.comments.activate(id)
            self.signal("comments.activate", id)
        else:
            with self.isso.lock:
                self.comments.delete(id)
            self.cache.delete('hash', (item['email'] or item['remote_addr']).encode('utf-8'))
            self.signal("comments.delete", id)

        return Response("Yo", 200)

    @requires(str, 'uri')
    def fetch(self, environ, request, uri):

        rv = list(self.comments.fetch(uri))
        if not rv:
            raise NotFound

        for item in rv:

            key = item['email'] or item['remote_addr']
            val = self.cache.get('hash', key.encode('utf-8'))

            if val is None:
                val = str(pbkdf2(key, self.isso.salt, 1000, 6))
                self.cache.set('hash', key.encode('utf-8'), val)

            item['hash'] = val

            for key in set(item.keys()) - API.FIELDS:
                item.pop(key)

        if request.args.get('plain', '0') == '0':
            for item in rv:
                item['text'] = markdown(item['text'])

        return JSON(json.dumps(rv), 200)

    @csrf
    def like(self, environ, request, id):

        nv = self.comments.vote(True, id, utils.anonymize(str(request.remote_addr)))
        return Response(json.dumps(nv), 200)

    @csrf
    def dislike(self, environ, request, id):

        nv = self.comments.vote(False, id, utils.anonymize(str(request.remote_addr)))
        return Response(json.dumps(nv), 200)

    @requires(str, 'uri')
    def count(self, environ, request, uri):

        rv = self.comments.count(uri)[0]

        if rv == 0:
            raise NotFound

        return JSON(json.dumps(rv), 200)

    def checkip(self, env, req):
        return Response(utils.anonymize(str(req.remote_addr)), 200)
