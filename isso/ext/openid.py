# -*- encoding: utf-8 -*-

import string
import json
import base64
import random

from isso import local
from isso.utils import http
from isso.utils.parse import urlsplit, urlunsplit, urlencode

from werkzeug.wsgi import get_current_url
from werkzeug.utils import redirect
from werkzeug.routing import Rule
from werkzeug.wrappers import Response
from werkzeug.exceptions import BadRequest

def rand_string(length):
    return ''.join(random.SystemRandom().choice(string.ascii_letters + string.digits) for n in range(length))

class OpenID(object):

    VIEWS = [
        ('login',       ('GET',  '/openid/login')),
        ('finalize',    ('GET',  '/openid/finalize')),
        ('logout',      ('GET',  '/openid/logout')),
    ]

    SESSION_LIFETIME = 4 * 3600

    FINAL_LOGIN_RESPONSE = """
        <!DOCTYPE html>
        <html>
            <head>
                <title>Login complete</title>
                <script>
                    var userinfo = {state: "%s", name: "%s", email: "%s", picture: "%s", website: "%s"};
                    window.opener.postMessage(userinfo, "%s");
                    window.close();
                </script>
            </head>
            <body>
            </body>
        </html>
"""

    def __init__(self, isso):
        self.isso = isso
        for (view, (method, path)) in self.VIEWS:
            isso.urls.add(Rule(path, methods=[method], endpoint=getattr(self, view)))

    def id_normalize(self, id_str):
        # Identifier normalization as per
        # http://openid.net/specs/openid-connect-discovery-1_0.html#IdentifierNormalization
        # Returns a tuple with the Normalized Identifier and the WebFinger Host
        url = urlsplit(id_str)
        if not url.hostname:
            return (None, None)
        scheme = url.scheme
        if not scheme:
            if url.username and url.hostname and not url.path and not url.query and not url.port and not url.fragment:
                scheme = "acct"
            else:
                scheme = "https"
        return (urlunsplit((scheme,) + url[1:4] + ("",)), url.netloc)

    def discovery(self, session):
        # Provider Discovery as per
        # http://openid.net/specs/openid-connect-discovery-1_0.html

        id_normed, wf_host = self.id_normalize(session['identifier'])
        params = {
            'resource': id_normed,
            'rel': "http://openid.net/specs/connect/1.0/issuer",
        }
        try:
            assert wf_host
            with http.curl("GET", "https://%s/.well-known/webfinger?%s" % (wf_host, urlencode(params))) as resp:
                assert resp and resp.getcode() == 200
                ans = json.loads(resp.read())
                for link in ans['links']:
                    if link['rel'] == "http://openid.net/specs/connect/1.0/issuer":
                        session['issuer'] = link['href']
                        u = urlsplit(session['issuer'])
                        assert u.scheme == "https"
                        assert u.hostname
                        assert not u.query and not u.fragment
                        break
                assert 'issuer' in session
        except (AssertionError, ValueError, KeyError):
               return False

        try:
            with http.curl("GET", session['issuer'].rstrip("/") + "/.well-known/openid-configuration") as resp:
                assert resp and resp.getcode() == 200
                ans = json.loads(resp.read())
                assert ans['issuer'] == session['issuer']
                session['registration_endpoint'] = ans['registration_endpoint']
                session['userinfo_endpoint'] = ans['userinfo_endpoint']
        except (AssertionError, ValueError, KeyError):
                return False

        return True

    def dyn_register(self, session):
        #  Dynamic Client Registration as per
        #  http://openid.net/specs/openid-connect-registration-1_0.html
        reg_data = {
            'client_name': "Isso",
            'redirect_uris': [session['redirect_uri']],
        }
        headers = {
            'Content-Type': "application/json",
        }
        try:
            with http.curl("POST", session['registration_endpoint'], body=json.dumps(reg_data), extra_headers=headers) as resp:
                # HTTP status should be 201 on success, but is returned as 200 from some implementations
                assert resp and 200 <= resp.getcode() < 300
                ans = json.loads(resp.read())
                session['client_id'] = ans['client_id']
                session['client_secret'] = ans['client_secret']
        except (AssertionError, ValueError, KeyError):
            return False

        return True

    def token_request(self, session):
        # Token Request as per
        # http://openid.net/specs/openid-connect-core-1_0.html#TokenEndpoint
        params = {
            'grant_type': "authorization_code",
            'code': session['code'],
            'redirect_uri': session['redirect_uri'],
        }
        auth_string = "%s:%s" % (session['client_id'], session['client_secret'])
        headers = {
            'Content-Type': "application/x-www-form-urlencoded",
            'Authorization': "Basic %s" % (base64.b64encode((auth_string.encode("ascii")).decode("ascii"))),
        }
        token_url = "%s/oauth/token" % (session['issuer'])
        try:
            with http.curl("POST", token_url, urlencode(params), extra_headers=headers) as resp:
                assert resp and resp.getcode() == 200
                ans = json.loads(resp.read())
                session['access_token'] = ans['access_token']
        except (AssertionError, ValueError, KeyError):
           return False

        return True

    def userinfo_request(self, session):
        # UserInfo Request as per
        # http://openid.net/specs/openid-connect-core-1_0.html#UserInfo
        headers = {
            'Authorization': "Bearer %s" % (session['access_token']),
        }
        try:
            with http.curl("GET", session['userinfo_endpoint'], extra_headers=headers) as resp:
                assert resp and resp.getcode() == 200
                session['userinfo'] = json.loads(resp.read())
        except (AssertionError, ValueError):
            return False

        return True

    def login(self, environ, request):
        cur_url = get_current_url(environ)
        session = {}
        session['identifier'] = request.args.get('isso-openid-identifier', '')
        session['redirect_uri'] = cur_url[:cur_url.rfind("/login")] + "/finalize"
        if not self.discovery(session):
            return BadRequest("OpenID Provider Discovery failed")
        if not self.dyn_register(session):
            return BadRequest("OpenID Dynamic Client Registration failed")

        session['id'] = rand_string(32)
        self.isso.db.openid_sessions.purge(self.SESSION_LIFETIME)
        self.isso.db.openid_sessions.add(session)
        params = {
            'response_type': "code",
            'scope': "openid profile email",
            'client_id': session['client_id'],
            'redirect_uri': session['redirect_uri'],
            'state': session['id'],
        }
        auth_url = "%s/oauth/auth?%s" % (session['issuer'], urlencode(params))
        return redirect(auth_url, code=303)

    def finalize(self, environ, request):
        cur_url = get_current_url(environ)
        session_id = request.args.get('state', '')
        session = self.isso.db.openid_sessions.get(session_id)
        if session is None:
            return BadRequest("Session expired or invalid")
        session['code'] = request.args.get('code', '')
        session['redirect_uri'] = cur_url
        session['redirect_uri'] = cur_url[:cur_url.rfind("/finalize")] + "/finalize"

        if not self.token_request(session):
            return BadRequest("OpenID Token Request failed")
        if not self.userinfo_request(session):
            return BadRequest("OpenID UserInfo Request failed")

        self.isso.db.openid_sessions.authorize(session_id)

        html = self.FINAL_LOGIN_RESPONSE % (session['id'],
                                            session['userinfo'].get('name', ""),
                                            session['userinfo'].get('email', ""),
                                            session['userinfo'].get('picture', ""),
                                            session['userinfo'].get('profile', False) or session['userinfo'].get('website', ""),
                                            local("origin"))
        return Response(html, 200, content_type="text/html")

    def logout(self, environ, request):
        session_id = request.args.get('state', '')
        self.isso.db.openid_sessions.delete(session_id);
        return Response("", 200)
