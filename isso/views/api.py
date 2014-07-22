# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import cgi
import functools

from itsdangerous import SignatureExpired, BadSignature

from werkzeug.http import dump_cookie
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from isso.compat import text_type as str, string_types

from isso import utils
from isso.utils import JSONResponse as JSON
from isso.views import requires
from isso.utils.hash import sha1

from isso.controllers import threads, comments


def normalize(url):
    if not url.startswith(("http://", "https://")):
        return "http://" + url
    return url


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

def auth(func):
    """A decorator to check the validity of an auth cookie."""

    def dec(self, env, req, *args, **kwargs):

        if not self.conf.getboolean("auth", "enabled"):
            return func(self, env, req, *args, **kwargs)
        try:
            self.load(req.cookies.get("auth", ""))
        except (SignatureExpired, BadSignature):
            raise Forbidden
        return func(self, env, req, *args, **kwargs)

    return dec

class API(object):

    # comment fields, that can be submitted
    ACCEPT = set(['text', 'author', 'email', 'website', 'parent'])

    def __init__(self, conf, cache, db, guard, hash, markup, signer):
        self.conf = conf

        self.db = db
        self.cache = cache

        self.hash = hash
        self.markup = markup

        self.threads = threads.Controller(db)
        self.comments = comments.Controller(db, guard)

        self.max_age = conf.getint("general", "max-age")
        self.moderated = conf.getboolean("moderation", "enabled")

        self.sign = signer.dumps
        self.load = functools.partial(signer.loads, max_age=self.max_age)

    def serialize(self, comment, markup=True):
        _id = str(comment.id)
        obj = {
            "id": comment.id, "parent": comment.parent,
            "mode": comment.mode,
            "created": comment.created, "modified": comment.modified,
            "text": comment.text, "author": comment.author,
            "email": comment.email, "website": comment.website,
            "likes": comment.likes, "dislikes": comment.dislikes}

        if markup:
            html = self.cache.get("text", _id)
            if html is None:
                html = self.markup.render(comment.text)
                self.cache.set("text", _id, html)
            obj["text"] = html

        hash = self.cache.get("hash", _id)
        if hash is None:
            hash = self.hash(comment.email or comment.remote_addr)
            self.cache.set("hash", _id, hash)
        obj["hash"] = hash

        return obj

    @xhr
    @auth
    @requires(str, 'uri')
    def new(self, environ, request, uri):
        data = request.get_json()

        if not isinstance(data, dict):
            raise BadRequest(400, "request data is not an object")

        for field in set(data.keys()) - API.ACCEPT:
            data.pop(field)

        for field in ("author", "email", "website"):
            if isinstance(data.get(field, None), string_types):
                data[field] = cgi.escape(data[field])

        if isinstance(data.get("website", None), string_types):
            data["website"] = normalize(data["website"])

        remote_addr = utils.anonymize(str(request.remote_addr))

        with self.db.transaction:
            thread = self.threads.get(uri)
            if thread is None:
                thread = self.threads.new(uri)
            try:
                comment = self.comments.new(remote_addr, thread, data,
                                            moderated=self.moderated)
            except comments.Invalid as ex:
                raise BadRequest(ex.message)
            except comments.Denied as ex:
                raise Forbidden(ex.message)

        # TODO queue new thread, send notification

        _id = str(comment.id)
        signature = self.sign([comment.id, sha1(comment.text)])

        resp = JSON(
            self.serialize(comment),
            202 if comment.moderated == 2 else 201)
        resp.headers.add("Set-Cookie", dump_cookie(_id, signature))
        resp.headers.add("X-Set-Cookie", dump_cookie("isso-" + _id, signature))
        return resp

    def view(self, environ, request, id):
        comment = self.comments.get(id)

        if comment is None:
            raise NotFound

        markup = request.args.get('plain', '0') == '0'

        return JSON(self.serialize(comment, markup), 200)

    @xhr
    def edit(self, environ, request, id):

        try:
            rv = self.load(request.cookies.get(str(id), ""))
        except (SignatureExpired, BadSignature):
            raise Forbidden

        if rv[0] != id:
            raise Forbidden

        comment = self.comments.get(id)
        if comment is None:
            raise NotFound

        # verify checksum, mallory might skip cookie deletion when
        # he deletes a comment
        if rv[1] != sha1(comment.text):
            raise Forbidden

        data = request.get_json()

        if not isinstance(data, dict):
            raise BadRequest(400, "request data is not an object")

        for field in set(data.keys()) - API.ACCEPT:
            data.pop(field)

        with self.db.transaction:
            comment = self.comments.edit(id, data)

        _id = str(comment.id)
        signature = self.sign([comment.id, sha1(comment.text)])

        self.cache.delete("text", _id)
        self.cache.delete("hash", _id)

        resp = JSON(self.serialize(comment), 200)
        resp.headers.add("Set-Cookie", dump_cookie(_id, signature))
        resp.headers.add("X-Set-Cookie", dump_cookie("isso-" + _id, signature))
        return resp

    @xhr
    def delete(self, environ, request, id, key=None):

        try:
            rv = self.load(request.cookies.get(str(id), ""))
        except (SignatureExpired, BadSignature):
            raise Forbidden

        if rv[0] != id:
            raise Forbidden

        comment = self.comments.get(id)
        if comment is None:
            raise NotFound

        if rv[1] != sha1(comment.text):
            raise Forbidden

        _id = str(comment.id)

        self.cache.delete("text", _id)
        self.cache.delete("hash", _id)

        with self.db.transaction:
            comment = self.comments.delete(id)

        cookie = functools.partial(dump_cookie, expires=0, max_age=0)

        resp = JSON(self.serialize(comment) if comment else None, 200)
        resp.headers.add("Set-Cookie", cookie(_id))
        resp.headers.add("X-Set-Cookie", cookie("isso-" + _id))
        return resp

    def moderate(self, environ, request, id, action, key):

        try:
            id = self.load(key, max_age=2**32)
        except (BadSignature, SignatureExpired):
            raise Forbidden

        comment = self.comments.get(id)
        if comment is None:
            raise NotFound

        if request.method == "GET":
            modal = (
                "<!DOCTYPE html>"
                "<html>"
                "<head>"
                "<script>"
                "  if (confirm('{0}: Are you sure?')) {"
                "      xhr = new XMLHttpRequest;"
                "      xhr.open('POST', window.location.href);"
                "      xhr.send(null);"
                "  }"
                "</script>".format(action.capitalize()))

            return Response(modal, 200, content_type="text/html")

        if action == "activate":
            with self.db.transaction:
                self.comments.activate(id)
        else:
            with self.db.transaction:
                self.comments.delete(id)

            self.cache.delete("text", str(comment.id))
            self.cache.delete("hash", str(comment.id))

        return Response("Ok", 200)

    # FIXME move logic into controller
    @requires(str, 'uri')
    def fetch(self, environ, request, uri):

        thread = self.threads.get(uri)
        if thread is None:
            raise NotFound

        args = {
            'thread': thread,
            'after': request.args.get('after', 0)
        }

        try:
            args['limit'] = int(request.args.get('limit'))
        except TypeError:
            args['limit'] = None
        except ValueError:
            return BadRequest("limit should be integer")

        if request.args.get('parent') is not None:
            try:
                args['parent'] = int(request.args.get('parent'))
                root_id = args['parent']
            except ValueError:
                return BadRequest("parent should be integer")
        else:
            args['parent'] = None
            root_id = None

        reply_counts = self.comments.reply_count(thread, after=args['after'])

        if args['limit'] == 0:
            root_list = []
        else:
            root_list = list(self.comments.all(**args))
            if not root_list:
                raise NotFound

        if root_id not in reply_counts:
            reply_counts[root_id] = 0

        try:
            nested_limit = int(request.args.get('nested_limit'))
        except TypeError:
            nested_limit = None
        except ValueError:
            return BadRequest("nested_limit should be integer")

        rv = {
            'id'             : root_id,
            'total_replies'  : reply_counts[root_id],
            'hidden_replies' : reply_counts[root_id] - len(root_list),
            'replies'        : self._process_fetched_list(root_list)
        }
        # We are only checking for one level deep comments
        if root_id is None:
            for comment in rv['replies']:
                if comment['id'] in reply_counts:
                    comment['total_replies'] = reply_counts[comment['id']]
                    if nested_limit is not None:
                        if nested_limit > 0:
                            args['parent'] = comment['id']
                            args['limit'] = nested_limit
                            replies = list(self.comments.all(**args))
                        else:
                            replies = []
                    else:
                        args['parent'] = comment['id']
                        replies = list(self.comments.all(**args))
                else:
                    comment['total_replies'] = 0
                    replies = []

                comment['hidden_replies'] = comment['total_replies'] - len(replies)
                comment['replies'] = self._process_fetched_list(replies)

        return JSON(rv, 200)

    def _process_fetched_list(self, fetched_list):
        return map(self.serialize, fetched_list)

    @xhr
    def like(self, environ, request, id):
        remote_addr = utils.anonymize(str(request.remote_addr))

        if not self.comments.like(remote_addr, id):
            raise BadRequest

        return Response("Ok", 200)

    @xhr
    def dislike(self, environ, request, id):
        remote_addr = utils.anonymize(str(request.remote_addr))

        if not self.comments.dislike(remote_addr, id):
            raise BadRequest

        return Response("Ok", 200)

    def count(self, environ, request):
        data = request.get_json()

        if not isinstance(data, list) and not all(isinstance(x, str) for x in data):
            raise BadRequest("JSON must be a list of URLs")

        th = [self.threads.get(uri) for uri in data]
        return JSON(self.comments.count(*th), 200)
