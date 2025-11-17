# -*- encoding: utf-8 -*-

import collections
import re
import time
import functools
import json  # json.dumps to put URL in <script>
import pkg_resources

from configparser import NoOptionError
from datetime import datetime, timedelta
from html import escape
from io import BytesIO as StringIO
from os import path as os_path
from urllib.parse import unquote, urlparse, urlsplit
from xml.etree import ElementTree as ET

from itsdangerous import SignatureExpired, BadSignature
from werkzeug.exceptions import BadRequest, Forbidden, NotFound
from werkzeug.http import dump_cookie
from werkzeug.routing import Rule
from werkzeug.utils import redirect, send_from_directory
from werkzeug.wrappers import Response
from werkzeug.wsgi import get_current_url

from isso import utils, local
from isso.utils import (http, parse,
                        JSONResponse as JSON, XMLResponse as XML,
                        render_template)
from isso.utils.hash import md5, sha1
from isso.views import requires


# from Django apparently, looks good to me *duck*
__url_re = re.compile(
    r'^'
    r'(https?://)?'
    # domain...
    r'(?:(?:[\w](?:[\w-]{0,61}[\w])?\.)+(?:[\w]{2,6}\.?|[\w-]{2,}\.?)|'
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)'
    r'$', re.IGNORECASE | re.UNICODE)


def isurl(text):
    return __url_re.match(text) is not None


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

    """
    @apiDefine csrf
    @apiHeader {String="application/json"} Content-Type
        The content type must be set to `application/json` to prevent CSRF attacks.
    """

    def dec(self, env, req, *args, **kwargs):

        if req.content_type and not req.content_type.startswith("application/json"):
            raise Forbidden("CSRF")
        return func(self, env, req, *args, **kwargs)

    return dec


def get_comment_id_from_url(comment_url):
    """
    Extracts the comment ID from a given comment URL.

    Args:
        comment_url (str): The URL of the comment.

    Returns:
        int or None: The extracted comment ID if successful, None otherwise.
    """
    try:
        # Parse the comment URL to extract the comment ID from the fragment
        parsed_url = urlsplit(comment_url)
    except ValueError:
        # Handle malformed URL
        return None

    fragment = parsed_url.fragment
    if not fragment or '-' not in fragment:
        # Handle missing fragment or fragment without hyphen
        return None

    last_element = fragment.split('-')[-1]
    try:
        comment_id = int(last_element)
    except ValueError:
        # Handle invalid comment ID
        return None

    return comment_id


def get_uri_from_url(url):
    try:
        # Parse the URL to extract the URI
        parsed_url = urlsplit(url)
    except ValueError:
        # Handle malformed URL
        return None

    uri = parsed_url.path
    if not uri:
        # Handle missing URI
        return None

    return uri


def requires_auth(method):
    def decorated(self, *args, **kwargs):
        request = args[1]
        auth = request.authorization
        if not auth:
            return Response(
                "Unauthorized", 401,
                {'WWW-Authenticate': 'Basic realm="Authentication Required"'})
        if not self.check_auth(auth.username, auth.password):
            return Response(
                "Wrong username or password", 401,
                {'WWW-Authenticate': 'Basic realm="Authentication Required"'})
        return method(self, *args, **kwargs)
    return decorated


def requires_admin(method):
    def decorated(self, *args, **kwargs):
        if not self.isso.conf.getboolean("admin", "enabled"):
            return NotFound(
                "Unavailable because 'admin' not enabled by site admin"
            )

        return method(self, *args, **kwargs)
    return decorated


class API(object):

    FIELDS = set(['id', 'parent', 'text', 'author', 'website',
                  'mode', 'created', 'modified', 'likes', 'dislikes', 'hash', 'gravatar_image', 'notification'])

    # comment fields, that can be submitted
    ACCEPT = set(['text', 'author', 'website', 'email', 'parent', 'title', 'notification'])

    VIEWS = [
        ('fetch', ('GET', '/')),
        ('new', ('POST', '/new')),
        ('counts', ('POST', '/count')),
        ('feed', ('GET', '/feed')),
        ('latest', ('GET', '/latest')),
        ('view', ('GET', '/id/<int:id>')),
        ('edit', ('PUT', '/id/<int:id>')),
        ('delete', ('DELETE', '/id/<int:id>')),
        ('unsubscribe', ('GET', '/id/<int:id>/unsubscribe/<string:email>/<string:key>')),
        ('moderate', ('GET', '/id/<int:id>/<any(edit,activate,delete):action>/<string:key>')),
        ('moderate', ('POST', '/id/<int:id>/<any(edit,activate,delete):action>/<string:key>')),
        ('like', ('POST', '/id/<int:id>/like')),
        ('dislike', ('POST', '/id/<int:id>/dislike')),
        ('demo', ('GET', '/demo/')),
        ('preview', ('POST', '/preview')),
        ('config', ('GET', '/config')),
        ('login', ('POST', '/login/')),
        ('admin', ('GET', '/admin/'))
    ]

    def __init__(self, isso, hasher):

        self.isso = isso
        self.hash = hasher.uhash
        self.cache = isso.cache
        self.signal = isso.signal

        self.conf = isso.conf.section("general")
        self.moderated = isso.conf.getboolean("moderation", "enabled")
        # this is similar to the wordpress setting "Comment author must have a previously approved comment"
        try:
            self.approve_if_email_previously_approved = isso.conf.getboolean("moderation", "approve-if-email-previously-approved")
        except NoOptionError:
            self.approve_if_email_previously_approved = False
        try:
            self.trusted_proxies = list(isso.conf.getiter("server", "trusted-proxies"))
        except NoOptionError:
            self.trusted_proxies = []

        # These configuration records can be read out by client
        self.public_conf = {}
        self.public_conf["reply-to-self"] = isso.conf.getboolean("guard", "reply-to-self")
        self.public_conf["require-email"] = isso.conf.getboolean("guard", "require-email")
        self.public_conf["require-author"] = isso.conf.getboolean("guard", "require-author")
        self.public_conf["reply-notifications"] = isso.conf.getboolean("general", "reply-notifications")
        self.public_conf["gravatar"] = isso.conf.getboolean("general", "gravatar")

        if self.public_conf["gravatar"]:
            self.public_conf["avatar"] = False

        self.public_conf["feed"] = False
        rss = isso.conf.section("rss")
        if rss and rss.get('base'):
            self.public_conf["feed"] = True

        self.guard = isso.db.guard
        self.threads = isso.db.threads
        self.comments = isso.db.comments

        for (view, (method, path)) in self.VIEWS:
            isso.urls.add(
                Rule(path, methods=[method], endpoint=getattr(self, view)))

    @classmethod
    def verify(cls, comment):

        if comment.get("text") is None:
            return False, "text is missing"

        if not isinstance(comment.get("parent"), (int, type(None))):
            return False, "parent must be an integer or null"

        for key in ("text", "author", "website", "email"):
            if not isinstance(comment.get(key), (str, type(None))):
                return False, "%s must be a string or null" % key

        if len(comment["text"].rstrip()) < 3:
            return False, "text is too short (minimum length: 3)"

        if len(comment["text"]) > 65535:
            return False, "text is too long (maximum length: 65535)"

        if len(comment.get("email") or "") > 254:
            return False, "http://tools.ietf.org/html/rfc5321#section-4.5.3"

        if comment.get("website"):
            if len(comment["website"]) > 254:
                return False, "arbitrary length limit"
            if not isurl(comment["website"]):
                return False, "Website not Django-conform"

        return True, ""

    # Common definitions for apidoc follow:
    """
    @apiDefine plainParam
    @apiQuery {Number=0,1} [plain=0]
        If set to `1`, the plain text entered by the user will be returned in the comments’ `text` attribute (instead of the rendered markdown).
    """
    """
    @apiDefine commentResponse

    @apiSuccess {Number} id
        The comment’s id (assigned by the server).
    @apiSuccess {Number} parent
        Id of the comment this comment is a reply to. `null` if this is a top-level-comment.
    @apiSuccess {Number=1,2,4} mode
        The comment’s mode:
        value | explanation
         ---  | ---
         `1`  | accepted: The comment was accepted by the server and is published.
         `2`  | in moderation queue: The comment was accepted by the server but awaits moderation.
         `4`  | deleted, but referenced: The comment was deleted on the server but is still referenced by replies.
    @apiSuccess {String} author
        The comments’s author’s name or `null`.
    @apiSuccess {String} website
        The comment’s author’s website or `null`.
    @apiSuccess {String} hash
        A hash uniquely identifying the comment’s author.
    @apiSuccess {Number} created
        UNIX timestamp of the time the comment was created (on the server).
    @apiSuccess {Number} modified
        UNIX timestamp of the time the comment was last modified (on the server). `null` if the comment was not yet modified.
    """
    """
    @apiDefine admin Admin access needed
        Only available to a logged-in site admin. Requires a valid `admin-session` cookie.
    """

    """
    @api {post} /new create new
    @apiGroup Comment
    @apiName new
    @apiVersion 0.12.6
    @apiDescription
        Creates a new comment. The server issues a cookie per new comment which acts as
        an authentication token to modify or delete the comment.
        The token is cryptographically signed and expires automatically after 900 seconds (=15min) by default.
    @apiUse csrf

    @apiQuery {String} uri
        The uri of the thread to create the comment on.
    @apiBody {String{3...65535}} text
        The comment’s raw text.
    @apiBody {String} [author]
        The comment’s author’s name.
    @apiBody {String{...254}} [email]
        The comment’s author’s email address.
    @apiBody {String{...254}} [website]
        The comment’s author’s website’s url. Must be Django-conform, i.e. either `http(s)://example.com/foo` or `example.com/`
    @apiBody {Number} [parent]
        The parent comment’s id if the new comment is a response to an existing comment.
    @apiBody {String} [title]
        The title of the thread. Required when creating the first comment for a new thread if the title cannot be automatically fetched from the URI.

    @apiExample {curl} Create a reply to comment with id 15:
        curl 'https://comments.example.com/new?uri=/thread/' -d '{"text": "Stop saying that! *isso*!", "author": "Max Rant", "email": "rant@example.com", "parent": 15}' -H 'Content-Type: application/json' -c cookie.txt

    @apiUse commentResponse

    @apiSuccessExample {json} Success after the above request:
        HTTP/1.1 201 CREATED
        Set-Cookie: 1=...; Expires=Wed, 18-Dec-2013 12:57:20 GMT; Max-Age=900; Path=/; SameSite=Lax
        X-Set-Cookie: isso-1=...; Expires=Wed, 18-Dec-2013 12:57:20 GMT; Max-Age=900; Path=/; SameSite=Lax
        {
            "website": null,
            "author": "Max Rant",
            "parent": 15,
            "created": 1464940838.254393,
            "text": "&lt;p&gt;Stop saying that! &lt;em&gt;isso&lt;/em&gt;!&lt;/p&gt;",
            "dislikes": 0,
            "modified": null,
            "mode": 1,
            "hash": "e644f6ee43c0",
            "id": 23,
            "likes": 0
        }
    """
    @xhr
    @requires(str, 'uri')
    def new(self, environ, request, uri):

        data = request.json

        for field in set(data.keys()) - API.ACCEPT:
            data.pop(field)

        for key in ("author", "email", "website", "parent"):
            data.setdefault(key, None)

        valid, reason = API.verify(data)
        if not valid:
            return BadRequest(reason)

        for field in ("author", "email", "website"):
            if data.get(field) is not None:
                data[field] = escape(data[field], quote=False)

        if data.get("website"):
            data["website"] = normalize(data["website"])

        data['mode'] = 2 if self.moderated else 1
        data['remote_addr'] = self._remote_addr(request)

        with self.isso.lock:
            if uri not in self.threads:
                if not data.get('title'):
                    with http.curl('GET', local("origin"), uri) as resp:
                        if resp and resp.status == 200:
                            uri, title = parse.thread(resp.read(), id=uri)
                        else:
                            return BadRequest(f'Cannot create new thread: URI {uri} is not accessible and no title was provided. Please provide a title parameter in your request.')
                else:
                    title = data['title']

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
            # if email-based auto-moderation enabled, check for previously approved author
            # right before approval.
            if self.approve_if_email_previously_approved and self.comments.is_previously_approved_author(data['email']):
                data['mode'] = 1

            rv = self.comments.add(uri, data)

        # notify extension, that the new comment has been successfully saved
        self.signal("comments.new:after-save", thread, rv)

        cookie = self.create_cookie(
            value=self.isso.sign([rv["id"], sha1(rv["text"])]),
            max_age=self.conf.getint('max-age'))

        rv["text"] = self.isso.render(rv["text"])
        rv["hash"] = self.hash(rv['email'] or rv['remote_addr'])

        self.cache.set(
            'hash', (rv['email'] or rv['remote_addr']).encode('utf-8'), rv['hash'])

        rv = self._add_gravatar_image(rv)

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        # success!
        self.signal("comments.new:finish", thread, rv)

        resp = JSON(rv, 202 if rv["mode"] == 2 else 201)
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    def _remote_addr(self, request):
        """Return the anonymized IP address of the requester.

        Takes into consideration a potential X-Forwarded-For HTTP header
        if a necessary server.trusted-proxies configuration entry is set.

        Recipe source: https://stackoverflow.com/a/22936947/636849
        """
        remote_addr = request.remote_addr
        if self.trusted_proxies:
            route = request.access_route + [remote_addr]
            remote_addr = next((addr for addr in reversed(route)
                                if addr not in self.trusted_proxies), remote_addr)
        return utils.anonymize(str(remote_addr))

    def create_cookie(self, **kwargs):
        """
        Setting cookies to SameSite=None requires "Secure" attribute.
        For http-only, we need to override the dump_cookie() default SameSite=None
        or the cookie will be rejected.
        https://developer.mozilla.org/en-US/docs/Web/HTTP/Headers/Set-Cookie/SameSite#samesitenone_requires_secure
        """
        isso_host_script = self.isso.conf.get("server", "public-endpoint") or local.host
        samesite = self.isso.conf.get("server", "samesite")
        if isso_host_script.startswith("https://"):
            secure = True
            samesite = samesite or "None"
        else:
            secure = False
            samesite = samesite or "Lax"
        return functools.partial(dump_cookie, **kwargs,
                                 secure=secure, samesite=samesite)

    """
    @api {get} /id/:id view
    @apiGroup Comment
    @apiName view
    @apiVersion 0.12.6
    @apiDescription
        View an existing comment, for the purpose of editing. Editing a comment is only possible for a short period of time (15min by default) after it was created and only if the requestor has a valid cookie for it. See the [Isso server documentation](https://isso-comments.de/docs/reference/server-config/) for details.

    @apiParam {Number} id
        The id of the comment to view.
    @apiUse plainParam

    @apiExample {curl} View the comment with id 4:
        curl 'https://comments.example.com/id/4' -b cookie.txt

    @apiUse commentResponse

    @apiSuccessExample Example result:
        {
            "website": null,
            "author": null,
            "parent": null,
            "created": 1464914341.312426,
            "text": " &lt;p&gt;I want to use MySQL&lt;/p&gt;",
            "dislikes": 0,
            "modified": null,
            "mode": 1,
            "id": 4,
            "likes": 1
        }
    """
    def view(self, environ, request, id):

        rv = self.comments.get(id)
        if rv is None:
            raise NotFound

        try:
            self.isso.unsign(request.cookies.get(str(id), ''))
        except (SignatureExpired, BadSignature):
            raise Forbidden

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        if request.args.get('plain', '0') == '0':
            rv['text'] = self.isso.render(rv['text'])

        return JSON(rv, 200)

    """
    @api {put} /id/:id edit
    @apiGroup Comment
    @apiName edit
    @apiVersion 0.12.6
    @apiDescription
        Edit an existing comment. Editing a comment is only possible for a short period of time (15min by default) after it was created and only if the requestor has a valid cookie for it. See the [Isso server documentation](https://isso-comments.de/docs/reference/server-config/) for details. Editing a comment will set a new edit cookie in the response.
    @apiUse csrf

    @apiParam {Number} id
        The id of the comment to edit.
    @apiBody {String{3...65535}} text
        A new (raw) text for the comment.
    @apiBody {String} [author]
        The modified comment’s author’s name.
    @apiBody {String{...254}} [website]
        The modified comment’s author’s website. Must be Django-conform, i.e. either `http(s)://example.com/foo` or `example.com/`

    @apiExample {curl} Edit comment with id 23:
        curl -X PUT 'https://comments.example.com/id/23' -d {"text": "I see your point. However, I still disagree.", "website": "maxrant.important.com"} -H 'Content-Type: application/json' -b cookie.txt

    @apiUse commentResponse

    @apiSuccessExample {json} Example response:
        HTTP/1.1 200 OK
        {
            "website": "maxrant.important.com",
            "author": "Max Rant",
            "parent": 15,
            "created": 1464940838.254393,
            "text": "&lt;p&gt;I see your point. However, I still disagree.&lt;/p&gt;",
            "dislikes": 0,
            "modified": 1464943439.073961,
            "mode": 1,
            "id": 23,
            "likes": 0
        }
    """
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

        data = request.json

        for key in set(data.keys()) - set(["text", "author", "website"]):
            data.pop(key)

        valid, reason = API.verify(data)
        if not valid:
            return BadRequest(reason)

        data['modified'] = time.time()

        with self.isso.lock:
            rv = self.comments.update(id, data)

        for key in set(rv.keys()) - API.FIELDS:
            rv.pop(key)

        self.signal("comments.edit", rv)

        cookie = self.create_cookie(
            value=self.isso.sign([rv["id"], sha1(rv["text"])]),
            max_age=self.conf.getint('max-age'))

        rv["text"] = self.isso.render(rv["text"])

        resp = JSON(rv, 200)
        resp.headers.add("Set-Cookie", cookie(str(rv["id"])))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % rv["id"]))
        return resp

    """
    @api {delete} /id/:id delete
    @apiGroup Comment
    @apiName delete
    @apiVersion 0.12.6
    @apiDescription
        Delete an existing comment. Deleting a comment is only possible for a short period of time (15min by default) after it was created and only if the requestor has a valid cookie for it. See the [Isso server documentation](https://isso-comments.de/docs/reference/server-config/) for details.
        Returns either `null` or a comment with an empty text value when the comment is still referenced by other comments.
    @apiUse csrf

    @apiParam {Number} id
        Id of the comment to delete.

    @apiExample {curl} Delete comment with id 14:
        curl -X DELETE 'https://comments.example.com/id/14' -b cookie.txt

    @apiSuccessExample Successful deletion returns null and deletes cookie:
        HTTP/1.1 200 OK
        Set-Cookie 14=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; SameSite=Lax
        X-Set-Cookie 14=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; SameSite=Lax

        null

    @apiSuccessExample {json} Comment still referenced by another:
        HTTP/1.1 200 OK
        Set-Cookie 14=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; SameSite=Lax
        X-Set-Cookie 14=; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Max-Age=0; Path=/; SameSite=Lax
        {
            "id": 14,
            "parent": null,
            "created": 1653432621.0512516,
            "modified": 1653434488.571937,
            "mode": 4,
            "text": "",
            "author": null,
            "website": null,
            "likes": 0,
            "dislikes": 0,
            "notification": 0
        }
    """
    @xhr
    def delete(self, environ, request, id):

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

        self.cache.delete(
            'hash', (item['email'] or item['remote_addr']).encode('utf-8'))

        with self.isso.lock:
            rv = self.comments.delete(id)

        if rv:
            for key in set(rv.keys()) - API.FIELDS:
                rv.pop(key)

        self.signal("comments.delete", id)

        resp = JSON(rv, 200)
        cookie = self.create_cookie(expires=0, max_age=0)

        resp.headers.add("Set-Cookie", cookie(str(id)))
        resp.headers.add("X-Set-Cookie", cookie("isso-%i" % id))
        return resp

    """
    @api {get} /id/:id/unsubscribe/:email/:key unsubscribe
    @apiGroup Comment
    @apiName unsubscribe
    @apiVersion 0.12.6
    @apiDescription
        Opt out from getting any further email notifications about replies to a particular comment. In order to use this endpoint, the requestor needs a `key` that is usually obtained from an email sent out by isso.

    @apiParam {Number} id
        The id of the comment to unsubscribe from replies to.
    @apiParam {String} email
        The email address of the subscriber.
    @apiParam {String} key
        The key to authenticate the subscriber.

    @apiExample {curl} Unsubscribe Alice from replies to comment with id 13:
        curl -X GET 'https://comments.example.com/id/13/unsubscribe/alice@example.com/WyJ1bnN1YnNjcmliZSIsImFsaWNlQGV4YW1wbGUuY29tIl0.DdcH9w.Wxou-l22ySLFkKUs7RUHnoM8Kos'

    @apiSuccessExample {html} Using GET:
        <!DOCTYPE html>
        <html>
            <head&gtSuccessfully unsubscribed</head>
            <body>
              <p>You have been unsubscribed from replies in the given conversation.</p>
            </body>
        </html>
    """
    def unsubscribe(self, environ, request, id, email, key):
        email = unquote(email)

        try:
            rv = self.isso.unsign(key, max_age=2**32)
        except (BadSignature, SignatureExpired):
            raise Forbidden

        if not isinstance(rv, list) or len(rv) != 2:
            raise Forbidden

        if rv[0] != 'unsubscribe' or rv[1] != email:
            raise Forbidden

        item = self.comments.get(id)

        if item is None:
            raise NotFound

        with self.isso.lock:
            self.comments.unsubscribe(email, id)

        modal = (
            "<!DOCTYPE html>"
            "<html>"
            "<head>"
            "  <title>Successfully unsubscribed</title>"
            "</head>"
            "<body>"
            "  <p>You have been unsubscribed from replies in the given conversation.</p>"
            "</body>"
            "</html>")

        return Response(modal, 200, content_type="text/html")

    """
    @api {post} /id/:id/:action/:key moderate
    @apiGroup Comment
    @apiName moderate
    @apiVersion 0.12.6
    @apiDescription
        Publish or delete a comment that is in the moderation queue (mode `2`). In order to use this endpoint, the requestor needs a `key` that is usually obtained from an email sent out by Isso or provided in the admin interface.
        This endpoint can also be used with a `GET` request. In that case, a html page is returned that asks the user whether they are sure to perform the selected action. If they select “yes”, the query is repeated using `POST`.

    @apiParam {Number} id
        The id of the comment to moderate.
    @apiParam {String=activate,edit,delete} action
        - `activate` to publish the comment (change its mode to `1`).
        - `edit`: Send `text`, `author`, `email` and `website` via `POST`.
           To be used from the admin interface. Better use the `edit` `PUT` endpoint.
        - `delete` to delete the comment.
    @apiParam {String} key
        The moderation key to authenticate the moderation.

    @apiExample {curl} delete comment with id 13:
        curl -X POST 'https://comments.example.com/id/13/delete/MTM.CjL6Fg.REIdVXa-whJS_x8ojQL4RrXnuF4'

    @apiSuccessExample {html} Request deletion using GET:
        <!DOCTYPE html>
        <html>
            <head>
                <script>
                    if (confirm('Delete: Are you sure?')) {
                        xhr = new XMLHttpRequest;
                        xhr.open('POST', window.location.href);
                        xhr.send(null);
                        xhr.onload = function() {
                            window.location.href = "https://example.com/example-thread/#isso-13";
                        };
                    }
                </script>

    @apiSuccessExample Delete using POST:
        Comment has been deleted

    @apiSuccessExample Activate using POST:
        Comment has been activated
    """
    def moderate(self, environ, request, id, action, key):
        try:
            id = self.isso.unsign(key, max_age=2**32)
        except (BadSignature, SignatureExpired):
            raise Forbidden

        item = self.comments.get(id)
        if item is None:
            raise NotFound

        thread = self.threads.get(item['tid'])
        link = local("origin") + thread["uri"] + "#isso-%i" % item["id"]

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
                "      xhr.onload = function() {"
                "          window.location.href = %s;"
                "      };"
                "  }"
                "</script>" % (action.capitalize(), json.dumps(link)))

            return Response(modal, 200, content_type="text/html")

        if action == "activate":
            if item['mode'] == 1:
                return Response("Already activated", 200)
            with self.isso.lock:
                self.comments.activate(id)
            self.signal("comments.activate", thread, item)
            return Response("Comment has been activated", 200)
        elif action == "edit":
            data = request.json
            with self.isso.lock:
                rv = self.comments.update(id, data)
            for key in set(rv.keys()) - API.FIELDS:
                rv.pop(key)
            self.signal("comments.edit", rv)
            return JSON(rv, 200)
        else:
            with self.isso.lock:
                self.comments.delete(id)
            self.cache.delete(
                'hash', (item['email'] or item['remote_addr']).encode('utf-8'))
            self.signal("comments.delete", id)
            return Response("Comment has been deleted", 200)

    """
    @api {get} / Get comments
    @apiGroup Thread
    @apiName fetch
    @apiVersion 0.13.1
    @apiDescription Queries the publicly visible comments of a thread.

    @apiQuery {String} uri
        The URI of thread to get the comments from.
    @apiQuery {Number} [parent]
        Return only comments that are children of the comment with the provided ID.
    @apiUse plainParam
    @apiQuery {Number} [limit]
        The maximum number of returned top-level comments. Omit for unlimited results.
    @apiQuery {Number} [nested_limit]
        The maximum number of returned nested comments per comment. Omit for unlimited results.
    @apiQuery {Number} [after]
        Includes only comments were added after the provided UNIX timestamp.
    @apiQuery {String} [sort]
        The sorting order of the comments. Possible values are `newest`, `oldest`, `upvotes`. If omitted, default sort order will be `oldest`.
    @apiQuery {Number} [offset]
        Offset the returned comments by this number. Used for pagination. Works only in combination with `limit`.

    @apiSuccess {Number} id
        Id of the comment `replies` is the list of replies of. `null` for the list of top-level comments.
    @apiSuccess {Number} total_replies
        The number of replies if the `limit` parameter was not set. If `after` is set to `X`, this is the number of comments that were created after `X`. So setting `after` may change this value!
    @apiSuccess {Number} hidden_replies
        The number of comments that were omitted from the results because of the `limit` request parameter. Usually, this will be `total_replies` - `limit`.
    @apiSuccess {Object[]} replies
        The list of comments. Each comment also has the `total_replies`, `replies`, `id` and `hidden_replies` properties to represent nested comments.
    @apiSuccess {Object[]} config
        Object holding only the client configuration parameters that depend on server settings. Will be dropped in a future version of Isso. Use the dedicated `/config` endpoint instead.

    @apiExample {curl} Get 2 comments with 5 responses:
        curl 'https://comments.example.com/?uri=/thread/&limit=2&nested_limit=5'
    @apiSuccessExample {json} Example response:
        {
          "total_replies": 14,
          "replies": [
            {
              "website": null,
              "author": null,
              "parent": null,
              "created": 1464818460.732863,
              "text": "&lt;p&gt;Hello, World!&lt;/p&gt;",
              "total_replies": 1,
              "hidden_replies": 0,
              "dislikes": 2,
              "modified": null,
              "mode": 1,
              "replies": [
                {
                  "website": null,
                  "author": null,
                  "parent": 1,
                  "created": 1464818460.769638,
                  "text": "&lt;p&gt;Hi, now some Markdown: &lt;em&gt;Italic&lt;/em&gt;, &lt;strong&gt;bold&lt;/strong&gt;, &lt;code&gt;monospace&lt;/code&gt;.&lt;/p&gt;",
                  "dislikes": 0,
                  "modified": null,
                  "mode": 1,
                  "hash": "2af4e1a6c96a",
                  "id": 2,
                  "likes": 2
                }
              ],
              "hash": "1cb6cc0309a2",
              "id": 1,
              "likes": 2
            },
            {
              "website": null,
              "author": null,
              "parent": null,
              "created": 1464818460.80574,
              "text": "&lt;p&gt;Lorem ipsum dolor sit amet, consectetur adipisicing elit. Accusantium at commodi cum deserunt dolore, error fugiat harum incidunt, ipsa ipsum mollitia nam provident rerum sapiente suscipit tempora vitae? Est, qui?&lt;/p&gt;",
              "total_replies": 0,
              "hidden_replies": 0,
              "dislikes": 0,
              "modified": null,
              "mode": 1,
              "replies": [],
              "hash": "1cb6cc0309a2",
              "id": 3,
              "likes": 0
            },
            "id": null,
            "hidden_replies": 12
        }
    """
    @requires(str, 'uri')
    def fetch(self, environ, request, uri):

        args = {
            'uri': uri,
            'after': request.args.get('after', 0)
        }

        # map sort query parameter
        valid_sort_options = ['newest', 'oldest', 'upvotes']
        sort = request.args.get('sort', 'oldest')

        if sort not in valid_sort_options:
            return BadRequest("Invalid sort option. Must be one of: 'newest', 'oldest', 'upvotes'")

        if sort == 'newest':
            args['order_by'] = 'created'
            args['asc'] = 0
        elif sort == 'oldest':
            args['order_by'] = 'created'
            args['asc'] = 1
        elif sort == 'upvotes':
            args['order_by'] = 'karma'
            args['asc'] = 0

        try:
            args['limit'] = int(request.args.get('limit'))
        except TypeError:
            args['limit'] = None
        except ValueError:
            return BadRequest("limit should be integer")

        try:
            args['offset'] = int(request.args.get('offset', 0))
            if args['offset'] < 0:
                return BadRequest("offset should not be negative")
        except (ValueError, TypeError):
            return BadRequest("offset should be integer")

        if request.args.get('parent') is not None:
            try:
                args['parent'] = int(request.args.get('parent'))
                root_id = args['parent']
            except ValueError:
                return BadRequest("parent should be integer")
        else:
            args['parent'] = None
            root_id = None

        plain = request.args.get('plain', '0') == '0'

        reply_counts = self.comments.reply_count(uri)

        if args['limit'] == 0:
            root_list = []
        else:
            root_list = list(self.comments.fetch(**args))

        if root_id not in reply_counts:
            reply_counts[root_id] = 0

        # We need to calculate the total number of comments for the root response value
        total_replies = sum(reply_counts.values()) if root_id is None else reply_counts[root_id]

        try:
            nested_limit = int(request.args.get('nested_limit'))
        except TypeError:
            nested_limit = None
        except ValueError:
            return BadRequest("nested_limit should be integer")

        rv = {
            'id': root_id,
            'total_replies': total_replies,
            'hidden_replies': reply_counts[root_id] - len(root_list) - args['offset'],
            'replies': self._process_fetched_list(root_list, plain),
            'config': self.public_conf
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
                            # Reset offset to 0 for nested comments to ensure correct pagination
                            args['offset'] = 0
                            replies = list(self.comments.fetch(**args))
                        else:
                            replies = []
                    else:
                        args['parent'] = comment['id']
                        replies = list(self.comments.fetch(**args))
                else:
                    comment['total_replies'] = 0
                    replies = []

                comment['hidden_replies'] = comment['total_replies'] - \
                    len(replies)
                comment['replies'] = self._process_fetched_list(replies, plain)

        return JSON(rv, 200)

    def _add_gravatar_image(self, item):
        if not self.conf.getboolean('gravatar'):
            return item

        email = item['email'] or item['author'] or ''
        email_md5_hash = md5(email)

        gravatar_url = self.conf.get('gravatar-url')
        item['gravatar_image'] = gravatar_url.format(email_md5_hash)

        return item

    def _process_fetched_list(self, fetched_list, plain=False):
        for item in fetched_list:

            key = item['email'] or item['remote_addr']
            val = self.cache.get('hash', key.encode('utf-8'))

            if val is None:
                val = self.hash(key)
                self.cache.set('hash', key.encode('utf-8'), val)

            item['hash'] = val

            item = self._add_gravatar_image(item)

            for key in set(item.keys()) - API.FIELDS:
                item.pop(key)

        if plain:
            for item in fetched_list:
                item['text'] = self.isso.render(item['text'])

        return fetched_list

    """
    @apiDefine likeResponse
    @apiSuccess {Number} likes
        The (new) number of likes on the comment.
    @apiSuccess {Number} dislikes
        The (new) number of dislikes on the comment.
    @apiSuccessExample Return updated vote counts:
        {
            "likes": 4,
            "dislikes": 3
        }
    """

    """
    @api {post} /id/:id/like like
    @apiGroup Comment
    @apiName like
    @apiVersion 0.12.6
    @apiDescription
         Puts a “like” on a comment. The author of a comment cannot like their own comment.
    @apiUse csrf

    @apiParam {Number} id
        The id of the comment to like.

    @apiExample {curl} Like comment with id 23:
        curl -X POST 'https://comments.example.com/id/23/like'

    @apiUse likeResponse
    """
    @xhr
    def like(self, environ, request, id):

        nv = self.comments.vote(True, id, self._remote_addr(request))
        return JSON(nv, 200)

    """
    @api {post} /id/:id/dislike dislike
    @apiGroup Comment
    @apiName dislike
    @apiVersion 0.12.6
    @apiDescription
         Puts a “dislike” on a comment. The author of a comment cannot dislike their own comment.
    @apiUse csrf

    @apiParam {Number} id
        The id of the comment to dislike.

    @apiExample {curl} Dislike comment with id 23:
        curl -X POST 'https://comments.example.com/id/23/dislike'

    @apiUse likeResponse
    """
    @xhr
    def dislike(self, environ, request, id):

        nv = self.comments.vote(False, id, self._remote_addr(request))
        return JSON(nv, 200)

    """
    @api {post} /preview preview
    @apiGroup Comment
    @apiName preview
    @apiVersion 0.12.6
    @apiDescription
        Render comment text using markdown.

    @apiBody {String{3...65535}} text
        (Raw) comment text

    @apiSuccess {String} text
        Rendered comment text

    @apiExample {curl} Preview comment:
        curl -X POST 'https://comments.example.com/preview' -d '{"text": "A sample comment"}'

    @apiSuccessExample {json} Rendered comment:
        {
            "text": "<p>A sample comment</p>"
        }
    """
    def preview(self, environment, request):
        data = request.json

        if data.get("text", None) is None:
            raise BadRequest("no text given")

        return JSON({'text': self.isso.render(data["text"])}, 200)

    """
    @api {post} /count Count comments
    @apiGroup Thread
    @apiName counts
    @apiVersion 0.12.6
    @apiDescription
        Counts the number of comments on multiple threads. The requestor provides a list of thread uris. The number of comments on each thread is returned as a list, in the same order as the threads were requested. The counts include comments that are responses to comments, but only published comments (i.e. exclusing comments pending moderation).

    @apiBody {Number[]} urls
        Array of URLs for which to fetch comment counts

    @apiExample {curl} Get the respective counts of 5 threads:
        curl -X POST 'https://comments.example.com/count' -d '["/blog/firstPost.html", "/blog/controversalPost.html", "/blog/howToCode.html", "/blog/boringPost.html", "/blog/isso.html"]

    @apiSuccessExample {json} Counts of 5 threads:
        [2, 18, 4, 0, 3]
    """
    def counts(self, environ, request):

        data = request.json

        if not isinstance(data, list) and not all(isinstance(x, str) for x in data):
            raise BadRequest("JSON must be a list of URLs")

        return JSON(self.comments.count(*data), 200)

    """
    @api {get} /feed Atom feed for comments
    @apiGroup Thread
    @apiName feed
    @apiVersion 0.12.6
    @apiDescription
        Provide an Atom feed for the given thread. Only available if `[rss] base` is set in server config. By default, up to 100 comments are returned.

    @apiQuery {String} uri
        The uri of the thread to display a feed for

    @apiExample {curl} Get an Atom feed for /thread/foo in XML format:
        curl 'https://comments.example.com/feed?uri=/thread/foo'

    @apiSuccessExample Atom feed for /thread/foo:
        <?xml version='1.0' encoding='utf-8'?>
        <feed xmlns="http://www.w3.org/2005/Atom" xmlns:thr="http://purl.org/syndication/thread/1.0">
          <updated>2022-05-24T20:38:04.032789Z</updated>
          <id>tag:example.com,2018:/isso/thread/thread/foo</id>
          <title>Comments for example.com/thread/foo</title>
          <entry>
            <id>tag:example.com,2018:/isso/1/2</id>
            <title>Comment #2</title>
            <updated>2022-05-24T20:38:04.032789Z</updated>
            <author>
              <name>John Doe</name>
            </author>
            <link href="http://example.com/thread/foo#isso-2" />
            <content type="html">&lt;p&gt;And another&lt;/p&gt;</content>
          </entry>
          <entry>
            <id>tag:example.com,2018:/isso/1/1</id>
            <title>Comment #1</title>
            <updated>2022-05-24T20:38:00.837703Z</updated>
            <author>
              <name>Jane Doe</name>
            </author>
            <link href="http://example.com/thread/foo#isso-1" />
            <content type="html">&lt;p&gt;A sample comment&lt;/p&gt;</content>
          </entry>
        </feed>
    """
    @requires(str, 'uri')
    def feed(self, environ, request, uri):
        conf = self.isso.conf.section("rss")
        if not conf.get('base'):
            raise NotFound

        args = {
            'uri': uri,
            'order_by': 'id',
            'asc': 0,
            'limit': conf.getint('limit')
        }
        try:
            args['limit'] = max(int(request.args.get('limit')), args['limit'])
        except TypeError:
            pass
        except ValueError:
            return BadRequest("limit should be integer")
        comments = self.comments.fetch(**args)
        base = conf.get('base').rstrip('/')
        hostname = urlparse(base).netloc

        # Let's build an Atom feed.
        #  RFC 4287: https://tools.ietf.org/html/rfc4287
        #  RFC 4685: https://tools.ietf.org/html/rfc4685 (threading extensions)
        #  For IDs: http://web.archive.org/web/20110514113830/http://diveintomark.org/archives/2004/05/28/howto-atom-id
        feed = ET.Element('feed', {
            'xmlns': 'http://www.w3.org/2005/Atom',
            'xmlns:thr': 'http://purl.org/syndication/thread/1.0'
        })

        # For feed ID, we would use thread ID, but we may not have
        # one. Therefore, we use the URI. We don't have a year
        # either...
        id = ET.SubElement(feed, 'id')
        id.text = 'tag:{hostname},2018:/isso/thread{uri}'.format(
            hostname=hostname, uri=uri)

        # For title, we don't have much either. Be pretty generic.
        title = ET.SubElement(feed, 'title')
        title.text = 'Comments for {hostname}{uri}'.format(
            hostname=hostname, uri=uri)

        comment0 = None

        for comment in comments:
            if comment0 is None:
                comment0 = comment

            entry = ET.SubElement(feed, 'entry')
            # We don't use a real date in ID either to help with
            # threading.
            id = ET.SubElement(entry, 'id')
            id.text = 'tag:{hostname},2018:/isso/{tid}/{id}'.format(
                hostname=hostname,
                tid=comment['tid'],
                id=comment['id'])
            title = ET.SubElement(entry, 'title')
            title.text = 'Comment #{}'.format(comment['id'])
            updated = ET.SubElement(entry, 'updated')
            updated.text = '{}Z'.format(datetime.fromtimestamp(
                comment['modified'] or comment['created']).isoformat())
            author = ET.SubElement(entry, 'author')
            name = ET.SubElement(author, 'name')
            name.text = comment['author']
            ET.SubElement(entry, 'link', {
                'href': '{base}{uri}#isso-{id}'.format(
                    base=base,
                    uri=uri, id=comment['id'])
            })
            content = ET.SubElement(entry, 'content', {
                'type': 'html',
            })
            content.text = self.isso.render(comment['text'])

            if comment['parent']:
                ET.SubElement(entry, 'thr:in-reply-to', {
                    'ref': 'tag:{hostname},2018:/isso/{tid}/{id}'.format(
                        hostname=hostname,
                        tid=comment['tid'],
                        id=comment['parent']),
                    'href': '{base}{uri}#isso-{id}'.format(
                        base=base,
                        uri=uri, id=comment['parent'])
                })

        # Updated is mandatory. If we have comments, we use the date
        # of last modification of the first one (which is the last
        # one). Otherwise, we use a fixed date.
        updated = ET.Element('updated')
        if comment0 is None:
            updated.text = '1970-01-01T01:00:00Z'
        else:
            updated.text = datetime.fromtimestamp(
                comment0['modified'] or comment0['created']).isoformat()
            updated.text += 'Z'
        feed.insert(0, updated)

        output = StringIO()
        ET.ElementTree(feed).write(output,
                                   encoding='utf-8',
                                   xml_declaration=True)
        response = XML(output.getvalue(), 200)

        # Add an etag/last-modified value for caching purpose
        if comment0 is None:
            response.set_etag('empty')
            response.last_modified = 0
        else:
            response.set_etag('{tid}-{id}'.format(**comment0))
            response.last_modified = comment0['modified'] or comment0['created']
        return response.make_conditional(request)

    """
    @api {get} /config Fetch client config
    @apiGroup Thread
    @apiName config
    @apiVersion 0.13.0
    @apiDescription
        Returns only the client configuration parameters that depend on server settings.

    @apiSuccess {Object[]} config
        The client configuration object.
    @apiSuccess {Boolean} config.reply-to-self
        Commenters can reply to their own comments.
    @apiSuccess {Boolean} config.require-author
        Commenters must enter valid Name.
    @apiSuccess {Boolean} config.require-email
        Commenters must enter valid email.
    @apiSuccess {Boolean} config.reply-notifications
        Enable reply notifications via E-mail.
    @apiSuccess {Boolean} config.gravatar
        Load images from Gravatar service instead of generating them. Also disables regular avatars (see below).
    @apiSuccess {Boolean} config.avatar
        To avoid having both regular avatars and Gravatars side-by-side,
        setting `gravatar` will disable regular avatars. The `avatar` key will
        only be sent by the server if `gravatar` is set.
    @apiSuccess {Boolean} config.feed
        Enable or disable the addition of a link to the feed for the comment
        thread.

    @apiExample {curl} get the client config:
        curl 'https://comments.example.com/config'

    @apiSuccessExample {json} Client config:
        {
          "config": {
            "reply-to-self": false,
            "require-email": false,
            "require-author": false,
            "reply-notifications": false,
            "gravatar": true,
            "avatar": false,
            "feed": false
          }
        }
    """
    def config(self, environment, request):
        rv = {'config': self.public_conf}
        return JSON(rv, 200)

    """
    @api {get} /demo/ Isso demo page
    @apiGroup Demo
    @apiName demo
    @apiVersion 0.13.0
    @apiPrivate
    @apiDescription
         Displays a demonstration of Isso with a thread counter and comment widget.

    @apiExample {curl} Get demo page
        curl 'https://comments.example.com/demo/'

    @apiSuccessExample {html} Demo page:
        <!DOCTYPE html>
        <head>
         <title>Isso Demo</title>
         <meta charset="utf-8">
         <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
         <div id="page">
          <div id="wrapper" style="max-width: 900px; margin-left: auto; margin-right: auto;">
           <h2><a href=".">Isso Demo</a></h2>
           <script src="../js/embed.dev.js" data-isso="../" ></script>
           <div>
             <p>This is a link to a thead, which will display a comment counter:
             <a href=".#isso-thread">How many Comments?</a></p>
             <p>Below is the actual comment field.</p>
           </div>
           <div id="isso-thread" data-title="Isso Test"><noscript>Javascript needs to be activated to view comments.</noscript></div>
          </div>
         </div>
        </body>
    """
    def demo(self, env, req):
        index = pkg_resources.resource_filename('isso', 'demo/index.html')
        return send_from_directory(os_path.dirname(index), 'index.html', env)

    """
    @api {post} /login/ Log in
    @apiGroup Admin
    @apiName login
    @apiVersion 0.12.6
    @apiPrivate
    @apiDescription
         Log in to admin, will redirect to `/admin/` on success. Must use form data, not `POST` JSON.

    @apiBody {String} password
        The admin password as set in `[admin] password` in the server config.

    @apiExample {curl} Log in
        curl -X POST 'https://comments.example.com/login' -F "password=strong_default_password_for_isso_admin" -c cookie.txt

    @apiSuccessExample {html} Login successful:
        <!doctype html>
        <html lang=en>
        <title>Redirecting...</title>
        <h1>Redirecting...</h1>
        <p>You should be redirected automatically to the target URL: <a href="https://comments.example.com/admin/">https://comments.example.com/admin/</a>. If not, click the link.
    """
    def login(self, env, req):
        if not self.isso.conf.getboolean("admin", "enabled"):
            isso_host_script = self.isso.conf.get("server", "public-endpoint") or local.host
            return render_template('disabled.html', isso_host_script=isso_host_script)
        data = req.form
        password = self.isso.conf.get("admin", "password")
        if data['password'] and data['password'] == password:
            response = redirect(re.sub(
                r'/login/$',
                '/admin/',
                get_current_url(env, strip_querystring=True)
            ))
            cookie = self.create_cookie(value=self.isso.sign({"logged": True}),
                                        expires=datetime.now() + timedelta(1))
            response.headers.add("Set-Cookie", cookie("admin-session"))
            response.headers.add("X-Set-Cookie", cookie("isso-admin-session"))
            return response
        else:
            isso_host_script = self.isso.conf.get("server", "public-endpoint") or local.host
            return render_template('login.html', isso_host_script=isso_host_script)

    """
    @api {get} /admin/ Admin interface
    @apiGroup Admin
    @apiName admin
    @apiVersion 0.12.6
    @apiPrivate
    @apiPermission admin
    @apiDescription
         Display an admin interface from which to manage comments. Will redirect to `/login` if not already logged in.

    @apiQuery {Number} [page=0]
        Page number
    @apiQuery {Number{1,2,4}} [mode=2]
        The comment’s mode:
        value | explanation
         ---  | ---
         `1`  | accepted: The comment was accepted by the server and is published.
         `2`  | in moderation queue: The comment was accepted by the server but awaits moderation.
         `4`  | deleted, but referenced: The comment was deleted on the server but is still referenced by replies.
    @apiQuery {String{id,created,modified,likes,dislikes,tid}} [order_by=created]
        Comment ordering
    @apiQuery {Number{0,1}} [asc=0]
        Ascending
    @apiQuery {String} comment_search_url
        Search comments by URL. Both threads and individual comments are valid.
        For example, a thread might have a URL like 'http://example.com/thread'
        and an individual comment might have a URL like 'http://example.com/thread#isso-1'

    @apiExample {curl} Listing of published comments:
        curl 'https://comments.example.com/admin/?mode=1&page=0&order_by=modified&asc=1' -b cookie.txt
    """
    def admin(self, env, req):
        isso_host_script = self.isso.conf.get("server", "public-endpoint") or local.host
        if not self.isso.conf.getboolean("admin", "enabled"):
            return render_template('disabled.html', isso_host_script=isso_host_script)
        try:
            data = self.isso.unsign(req.cookies.get('admin-session', ''),
                                    max_age=60 * 60 * 24)
        except BadSignature:
            return render_template('login.html', isso_host_script=isso_host_script)
        if not data or not data['logged']:
            return render_template('login.html', isso_host_script=isso_host_script)
        page_size = 100
        page = int(req.args.get('page', 0))
        order_by = req.args.get('order_by', 'created')
        asc = int(req.args.get('asc', 0))
        mode = int(req.args.get('mode', 2))
        comment_search_url = req.args.get('comment_search_url', '')

        # Search for comments by URL
        if comment_search_url:
            comment_id = get_comment_id_from_url(comment_search_url)
            uri = get_uri_from_url(comment_search_url)
            if comment_id or uri:
                comments = self.comments.fetchall(comment_id=comment_id, thread_uri=uri)
            else:
                comments = []
        else:
            comments = self.comments.fetchall(mode=mode, page=page,
                                              limit=page_size,
                                              order_by=order_by,
                                              asc=asc)
        comments_enriched = []
        for comment in list(comments):
            comment['hash'] = self.isso.sign(comment['id'])
            comments_enriched.append(comment)
        comment_mode_count = self.comments.count_modes()
        max_page = int(sum(comment_mode_count.values()) / 100)
        return render_template('admin.html', comments=comments_enriched,
                               page=int(page), mode=int(mode),
                               conf=self.conf, max_page=max_page,
                               counts=comment_mode_count,
                               order_by=order_by, asc=asc,
                               comment_search_url=comment_search_url,
                               isso_host_script=isso_host_script)
    """
    @api {get} /latest latest
    @apiGroup Comment
    @apiName latest
    @apiVersion 0.12.6
    @apiDescription
        Get the latest comments from the system, no matter which thread. Only available if `[general] latest-enabled` is set to `true` in server config.

    @apiQuery {Number} limit
        The quantity of last comments to retrieve

    @apiQuery {Number{1,2}} [mode=1]
        The comments’ mode:
        value | explanation
         ---  | ---
         `1`  | accepted: The comment was accepted by the server and is published.
         `2`  | in moderation queue: The comment was accepted by the server but awaits moderation.

    @apiExample {curl} Get the latest 5 accepted comments
        curl 'https://comments.example.com/latest?limit=5'

    @apiUse commentResponse

    @apiSuccessExample Example result:
        [
            {
                "website": null,
                "uri": "/some",
                "author": null,
                "parent": null,
                "created": 1464912312.123416,
                "text": " &lt;p&gt;I want to use MySQL&lt;/p&gt;",
                "dislikes": 0,
                "modified": null,
                "mode": 1,
                "id": 3,
                "likes": 1
            },
            {
                "website": null,
                "uri": "/other",
                "author": null,
                "parent": null,
                "created": 1464914341.312426,
                "text": " &lt;p&gt;I want to use MySQL&lt;/p&gt;",
                "dislikes": 0,
                "modified": null,
                "mode": 1,
                "id": 4,
                "likes": 0
            }
        ]
    """
    def latest(self, environ, request):
        # if the feature is not allowed, don't present the endpoint
        if not self.conf.getboolean("latest-enabled"):
            return NotFound(
                "Unavailable because 'latest-enabled' not set by site admin"
            )

        mode = request.args.get('mode', "1")

        if mode != "1" and mode != "2":
            return BadRequest(
                "Mode must either be '1' for accepted comments or '2' for pedning comments waiting moderation"
            )

        return self._latest(environ, request, mode)

    def check_auth(self, username, password):
        admin_password = self.isso.conf.get("admin", "password")

        return username == 'admin' and password == admin_password

    def _latest(self, environ, request, mode):
        # get and check the limit
        bad_limit_msg = "Query parameter 'limit' is mandatory (integer, >0)"
        try:
            limit = int(request.args['limit'])
        except (KeyError, ValueError):
            return BadRequest(bad_limit_msg)
        if limit <= 0:
            return BadRequest(bad_limit_msg)

        # retrieve the latest N comments from the DB
        all_comments_gen = self.comments.fetchall(limit=None, order_by='created', mode=mode)
        comments = collections.deque(all_comments_gen, maxlen=limit)

        # prepare a special set of fields (except text which is rendered specifically)
        fields = {
            'author',
            'created',
            'dislikes',
            'id',
            'likes',
            'mode',
            'modified',
            'parent',
            'text',
            'uri',
            'website',
        }

        # process the retrieved comments and build results
        result = []
        for comment in comments:
            processed = {key: comment[key] for key in fields}
            processed['text'] = self.isso.render(comment['text'])
            result.append(processed)

        return JSON(result, 200)
