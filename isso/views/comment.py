# -*- encoding: utf-8 -*-

import cgi
import json
import time
import hashlib
import logging
import functools

from itsdangerous import SignatureExpired, BadSignature

from werkzeug.http import dump_cookie
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest, Forbidden, NotFound

from isso.compat import text_type as str

from isso import utils, notify, db
from isso.utils import http, parse
from isso.crypto import pbkdf2

logger = logging.getLogger("isso")

FIELDS = set(['id', 'parent', 'text', 'author', 'website', 'email', 'mode',
              'created', 'modified', 'likes', 'dislikes', 'hash'])


class requires:

    def __init__(self, type, param):
        self.param = param
        self.type = type

    def __call__(self, func):
        def dec(app, env, req, *args, **kwargs):

            if self.param not in req.args:
                raise BadRequest("missing %s query" % self.param)

            try:
                kwargs[self.param] = self.type(req.args[self.param])
            except TypeError:
                raise BadRequest("invalid type for %s, expected %s" % (self.param, self.type))

            return func(app, env, req, *args, **kwargs)

        return dec


@requires(str, 'uri')
def new(app, environ, request, uri):

    data = request.get_json()

    for field in set(data.keys()) - set(['text', 'author', 'website', 'email', 'parent']):
        data.pop(field)

    if "text" not in data or data["text"] is None or len(data["text"]) < 3:
        raise BadRequest("no text given")

    if "id" in data and not isinstance(data["id"], int):
        raise BadRequest("parent id must be an integer")

    if len(data.get("email") or "") > 254:
        raise BadRequest("http://tools.ietf.org/html/rfc5321#section-4.5.3")

    for field in ("author", "email"):
        if data.get(field):
            data[field] = cgi.escape(data[field])

    data['mode'] = (app.conf.getboolean('moderation', 'enabled') and 2) or 1
    data['remote_addr'] = utils.anonymize(str(request.remote_addr))

    with app.lock:
        if uri not in app.db.threads:
            for host in app.conf.getiter('general', 'host'):
                with http.curl('GET', host, uri) as resp:
                    if resp and resp.status == 200:
                        title = parse.title(resp.read())
                        break
            else:
                return Response('URI does not exist', 404)

            app.db.threads.new(uri, title)
            logger.info('new thread: %s -> %s', uri, title)
        else:
            title = app.db.threads[uri].title

    try:
        with app.lock:
            rv = app.db.comments.add(uri, data)
    except db.IssoDBException:
        raise Forbidden

    host = list(app.conf.getiter('general', 'host'))[0].rstrip("/")
    href = host + uri + "#isso-%i" % rv["id"]

    deletion = host + environ["SCRIPT_NAME"] + "/delete/" + app.sign(str(rv["id"]))
    activation = None

    if app.conf.getboolean('moderation', 'enabled'):
        activation = host + environ["SCRIPT_NAME"] + "/activate/" + app.sign(str(rv["id"]))

    app.notify(title, notify.format(rv, href, utils.anonymize(str(request.remote_addr)),
                                    activation_key=activation, deletion_key=deletion))

    # save checksum of text into cookie, so mallory can't modify/delete a comment, if
    # he add a comment, then removed it but not the signed cookie.
    checksum = hashlib.md5(rv["text"].encode('utf-8')).hexdigest()

    rv["text"] = app.markdown(rv["text"])
    rv["hash"] = str(pbkdf2(rv['email'] or rv['remote_addr'], app.salt, 1000, 6))

    app.cache.set('hash', (rv['email'] or rv['remote_addr']).encode('utf-8'), rv['hash'])

    for key in set(rv.keys()) - FIELDS:
        rv.pop(key)

    # success!
    logger.info('comment created: %s', json.dumps(rv))

    cookie = functools.partial(dump_cookie,
        value=app.sign([rv["id"], checksum]),
        max_age=app.conf.getint('general', 'max-age'))

    resp = Response(json.dumps(rv), 202 if rv["mode"] == 2 else 201, content_type='application/json')
    resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
    resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
    return resp


def single(app, environ, request, id):

    if request.method == 'GET':
        rv = app.db.comments.get(id)
        if rv is None:
            raise NotFound

        for key in set(rv.keys()) - FIELDS:
            rv.pop(key)

        if request.args.get('plain', '0') == '0':
            rv['text'] = app.markdown(rv['text'])

        return Response(json.dumps(rv), 200, content_type='application/json')

    try:
        rv = app.unsign(request.cookies.get(str(id), ''))
    except (SignatureExpired, BadSignature):
        try:
            rv = app.unsign(request.cookies.get('admin', ''))
        except (SignatureExpired, BadSignature):
            raise Forbidden

    if rv[0] != id:
        raise Forbidden

    # verify checksum, mallory might skip cookie deletion when he deletes a comment
    if rv[1] != hashlib.md5(app.db.comments.get(id)["text"].encode('utf-8')).hexdigest():
        raise Forbidden

    if request.method == 'PUT':
        data = request.get_json()

        if "text" not in data or data["text"] is None or len(data["text"]) < 3:
            raise BadRequest("no text given")

        for key in set(data.keys()) - set(["text", "author", "website"]):
            data.pop(key)

        data['modified'] = time.time()

        with app.lock:
            rv = app.db.comments.update(id, data)

        for key in set(rv.keys()) - FIELDS:
            rv.pop(key)

        logger.info('comment %i edited: %s', id, json.dumps(rv))

        checksum = hashlib.md5(rv["text"].encode('utf-8')).hexdigest()
        rv["text"] = app.markdown(rv["text"])

        cookie = functools.partial(dump_cookie,
                value=app.sign([rv["id"], checksum]),
                max_age=app.conf.getint('general', 'max-age'))

        resp = Response(json.dumps(rv), 200, content_type='application/json')
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    if request.method == 'DELETE':

        item = app.db.comments.get(id)
        app.cache.delete('hash', (item['email'] or item['remote_addr']).encode('utf-8'))

        rv = app.db.comments.delete(id)
        if rv:
            for key in set(rv.keys()) - FIELDS:
                rv.pop(key)

        logger.info('comment %i deleted', id)

        cookie = functools.partial(dump_cookie, expires=0, max_age=0)

        resp = Response(json.dumps(rv), 200, content_type='application/json')
        resp.headers.add("Set-Cookie", cookie(str(id)))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % id))
        return resp


@requires(str, 'uri')
def fetch(app, environ, request, uri):

    rv = list(app.db.comments.fetch(uri))
    if not rv:
        raise NotFound

    for item in rv:

        key = item['email'] or item['remote_addr']
        val = app.cache.get('hash', key.encode('utf-8'))

        if val is None:
            val = str(pbkdf2(key, app.salt, 1000, 6))
            app.cache.set('hash', key.encode('utf-8'), val)

        item['hash'] = val

        for key in set(item.keys()) - FIELDS:
            item.pop(key)

    if request.args.get('plain', '0') == '0':
        for item in rv:
            item['text'] = app.markdown(item['text'])

    return Response(json.dumps(rv), 200, content_type='application/json')


def like(app, environ, request, id):

    nv = app.db.comments.vote(True, id, utils.anonymize(str(request.remote_addr)))
    return Response(json.dumps(nv), 200)


def dislike(app, environ, request, id):

    nv = app.db.comments.vote(False, id, utils.anonymize(str(request.remote_addr)))
    return Response(json.dumps(nv), 200)


@requires(str, 'uri')
def count(app, environ, request, uri):

    rv = app.db.comments.count(uri)[0]

    if rv == 0:
        raise NotFound

    return Response(json.dumps(rv), 200, content_type='application/json')


def activate(app, environ, request, auth):

    try:
        id = app.unsign(auth, max_age=2**32)
    except (BadSignature, SignatureExpired):
        raise Forbidden

    with app.lock:
        app.db.comments.activate(id)

    logger.info("comment %s activated" % id)
    return Response("Yo", 200)

def delete(app, environ, request, auth):

    try:
        id = app.unsign(auth, max_age=2**32)
    except (BadSignature, SignatureExpired):
        raise Forbidden

    with app.lock:
        app.db.comments.delete(id)

    logger.info("comment %s deleted" % id)
    return Response("%s successfully removed" % id)


def checkip(app, env, req):
    return Response(utils.anonymize(str(req.remote_addr)), 200)
