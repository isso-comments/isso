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
from werkzeug.wsgi import get_current_url
from werkzeug.utils import redirect

from isso.compat import text_type as str

from isso import utils, local
from isso.utils import http, parse, JSONResponse as JSON
from isso.utils.crypto import pbkdf2
from isso.views import requires


def sha1(text):
    return hashlib.sha1(text.encode('utf-8')).hexdigest()


def xhr(func):
    """A decorator to check for CSRF on POST/PUT/DELETE using a <form>
    element and JS to execute automatically (see #40 for a proof-of-concept).

    When an attacker uses a <form> to downvote a comment, the browser *should*
    add a `Content-Type: ...` header with three possible values:

    * application/x-www-form-urlencoded
    * multipart/form-data
    * text/plain

    If the header is not sent or requests `application/json`, the request is
    not forged (XHR is restricted by CORS separately).
    """

    def dec(self, env, req, *args, **kwargs):

        if req.content_type and not req.content_type.startswith("application/json"):
            raise Forbidden("CSRF")
        return func(self, env, req, *args, **kwargs)

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
        ('counts',  ('POST', '/count')),
        ('view',    ('GET', '/id/<int:id>')),
        ('edit',    ('PUT', '/id/<int:id>')),
        ('delete',  ('DELETE', '/id/<int:id>')),
        ('moderate',('GET',  '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
        ('moderate',('POST', '/id/<int:id>/<any(activate,delete):action>/<string:key>')),
        ('like',    ('POST', '/id/<int:id>/like')),
        ('dislike', ('POST', '/id/<int:id>/dislike')),
        ('checkip', ('GET', '/check-ip')),
        ('demo',    ('GET', '/demo'))
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

        if len(comment["text"].rstrip()) < 3:
            return False, "text is too short (minimum length: 3)"

        if len(comment.get("email") or "") > 254:
            return False, "http://tools.ietf.org/html/rfc5321#section-4.5.3"

        return True, ""

    @xhr
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
                        uri, title = parse.thread(resp.read(), id=uri)
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
            value=self.isso.sign([rv["id"], sha1(rv["text"])]),
            max_age=self.conf.getint('max-age'))

        rv["text"] = self.isso.render(rv["text"])
        rv["hash"] = pbkdf2(rv['email'] or rv['remote_addr'], self.isso.salt, 1000, 6).decode("utf-8")

        self.cache.set('hash', (rv['email'] or rv['remote_addr']).encode('utf-8'), rv['hash'])

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        # success!
        self.signal("comments.new:finish", thread, rv)

        resp = JSON(rv, 202 if rv["mode"] == 2 else 201)
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
            rv['text'] = self.isso.render(rv['text'])

        return JSON(rv, 200)

    @xhr
    def edit(self, environ, request, id):

        try:
            rv = self.isso.unsign(request.cookies.get(str(id), ''))
        except (SignatureExpired, BadSignature):
            raise Forbidden

        if rv[0] != id:
            raise Forbidden

        # verify checksum, mallory might skip cookie deletion when he deletes a comment
        if rv[1] != sha1(self.comments.get(id)["text"]):
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
                value=self.isso.sign([rv["id"], sha1(rv["text"])]),
                max_age=self.conf.getint('max-age'))

        rv["text"] = self.isso.render(rv["text"])

        resp = JSON(rv, 200)
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    @xhr
    def delete(self, environ, request, id, key=None):

        try:
            rv = self.isso.unsign(request.cookies.get(str(id), ""))
        except (SignatureExpired, BadSignature):
            raise Forbidden
        else:
            if rv[0] != id:
                raise Forbidden

            # verify checksum, mallory might skip cookie deletion when he deletes a comment
            if rv[1] != sha1(self.comments.get(id)["text"]):
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

        resp = JSON(rv, 200)
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

        fetch_args={'uri': uri}
        if request.args.get('after'):
            fetch_args['after'] = request.args.get('after')
            after = request.args.get('after')
        else:
            after = 0
        if request.args.get('limit'):
            try:
                fetch_args['limit'] = int(request.args.get('limit'))
            except ValueError:
                return BadRequest("limit should be integer")

        if request.args.get('parent'):
            parent_arg = request.args.get('parent')
            if parent_arg == 'NULL':
                fetch_args['parent'] = parent_arg
                root_id = None
            else:
                try:
                    fetch_args['parent'] = int(parent_arg)
                    root_id = int(parent_arg)
                except ValueError:
                    return BadRequest("parent should be integer or NULL")
        else:
            fetch_args['parent'] = 'NULL'
            root_id = None

        if request.args.get('plain', '0') == '0':
            plain = True
        else:
            plain = False

        reply_counts = self.comments.reply_count(uri, after)

        if 'limit' in fetch_args and fetch_args['limit'] == 0:
            root_list = []
        else:
            root_list = list(self.comments.fetch(**fetch_args))
            if not root_list:
                raise NotFound
        if root_id not in reply_counts:
            reply_counts[root_id] = 0

        if request.args.get('nested_limit'):
            try:
                nested_limit = int(request.args.get('nested_limit'))
            except ValueError:
                return BadRequest("nested_limit should be integer")
        else:
            nested_limit = None

        rv = {
            'id'             : root_id,
            'total_replies'  : reply_counts[root_id],
            'hidden_replies' : reply_counts[root_id] - len(root_list),
            'replies'        : self.process_fetched_list(root_list, plain)
        }
        # We are only checking for one level deep comments
        if root_id is None:
            for comment in rv['replies']:
                if comment['id'] in reply_counts:
                    comment['total_replies'] = reply_counts[comment['id']]
                    if nested_limit is not None:
                        if nested_limit > 0:
                            fetch_args['parent'] = comment['id']
                            fetch_args['limit'] = nested_limit
                            replies = list(self.comments.fetch(**fetch_args))
                        else:
                            replies = []
                    else:
                        fetch_args['parent'] = comment['id']
                        replies = list(self.comments.fetch(**fetch_args))
                else:
                    comment['total_replies'] = 0
                    replies = []
                comment['hidden_replies'] = comment['total_replies'] - len(replies)
                comment['replies'] = self.process_fetched_list(replies, plain)

        return JSON(rv, 200)

    def process_fetched_list(self, fetched_list, plain=False):
        for item in fetched_list:

            key = item['email'] or item['remote_addr']
            val = self.cache.get('hash', key.encode('utf-8'))

            if val is None:
                val = pbkdf2(key, self.isso.salt, 1000, 6).decode("utf-8")
                self.cache.set('hash', key.encode('utf-8'), val)

            item['hash'] = val

            for key in set(item.keys()) - API.FIELDS:
                item.pop(key)

        if plain:
            for item in fetched_list:
                item['text'] = self.isso.render(item['text'])

        return fetched_list

    @xhr
    def like(self, environ, request, id):

        nv = self.comments.vote(True, id, utils.anonymize(str(request.remote_addr)))
        return JSON(nv, 200)

    @xhr
    def dislike(self, environ, request, id):

        nv = self.comments.vote(False, id, utils.anonymize(str(request.remote_addr)))
        return JSON(nv, 200)

    # TODO: remove someday (replaced by :func:`counts`)
    @requires(str, 'uri')
    def count(self, environ, request, uri):

        rv = self.comments.count(uri)[0]

        if rv == 0:
            raise NotFound

        return JSON(rv, 200)

    def counts(self, environ, request):

        data = request.get_json()

        if not isinstance(data, list) and not all(isinstance(x, str) for x in data):
            raise BadRequest("JSON must be a list of URLs")

        return JSON(self.comments.count(*data), 200)

    def checkip(self, env, req):
        return Response(utils.anonymize(str(req.remote_addr)), 200)

    def demo(self, env, req):
        return redirect(get_current_url(env) + '/index.html')
