# -*- encoding: utf-8 -*-

import json
import os
import re
import tempfile
import time
import unittest

from unittest import mock
from urllib.parse import urlencode

from itsdangerous import URLSafeTimedSerializer
from itsdangerous.timed import TimestampSigner
from werkzeug.wrappers import Response

from isso import Isso, core, config
from isso.db import SQLite3
from isso.utils import http, NO_CACHE_HEADERS
from isso.views import comments
from isso.db.comments import VERIFICATION_LINK_MAX_AGE, VERIFICATION_RATE_WINDOW

from fixtures import curl, loads, FakeIP, FakeHost, JSONClient

http.curl = curl


class TestComments(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")
        conf.set("general", "latest-enabled", "true")
        self.conf = conf

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete

    def tearDown(self):
        os.unlink(self.path)

    def testGet(self):
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        r = self.get("/id/1")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)

        self.assertEqual(rv["id"], 1)
        self.assertEqual(rv["text"], "<p>Lorem ipsum ...</p>")

    def testCreate(self):
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)

        rv = loads(rv.data)

        self.assertEqual(rv["mode"], 1)
        self.assertEqual(rv["text"], "<p>Lorem ipsum ...</p>")

    def testWebsiteXSSPayloadIsEscaped(self):
        """Website field with XSS payload must have quotes HTML-escaped."""
        payload = "http://x.com/?'onmouseover='alert(document.domain)'x='"
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Hello", "website": payload}))
        self.assertEqual(rv.status_code, 201)
        rv = loads(rv.data)
        # Single quotes must be HTML-escaped so they cannot break out of an
        # HTML attribute context (e.g. href='...')
        self.assertNotIn("'", rv["website"])
        self.assertNotIn('"', rv["website"])
        self.assertEqual(
            rv["website"],
            "http://x.com/?&#x27;onmouseover=&#x27;alert(document.domain)&#x27;x=&#x27;",
        )

    def textCreateWithNonAsciiText(self):
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Здравствуй, мир!"}))

        self.assertEqual(rv.status_code, 201)
        rv = loads(rv.data)

        self.assertEqual(rv["mode"], 1)
        self.assertEqual(rv["text"], "<p>Здравствуй, мир!</p>")

    def testCreateMultiple(self):
        a = self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        b = self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        c = self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        self.assertEqual(loads(a.data)["id"], 1)
        self.assertEqual(loads(b.data)["id"], 2)
        self.assertEqual(loads(c.data)["id"], 3)

    def testCreateAndGetMultiple(self):
        for i in range(20):
            self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Spam"}))

        r = self.get("/?uri=%2Fpath%2F")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 20)
        self.assertEqual(rv["total_replies"], 20)

    def testCreateInvalidParent(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))
        invalid = self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 2}))

        self.assertEqual(loads(invalid.data)["parent"], 1)

    def testCreateInvalidThreadForParent(self):
        self.post("/new?uri=one", data=json.dumps({"text": "..."}))
        # Parent which is not in same thread should be rejected, set to None
        invalid = self.post("/new?uri=two", data=json.dumps({"text": "...", "parent": 1}))
        # Replies to commments in thread "two" are valid
        valid = self.post("/new?uri=two", data=json.dumps({"text": "...", "parent": 2}))

        self.assertEqual(loads(invalid.data)["parent"], None)
        self.assertEqual(loads(valid.data)["parent"], 2)

        # Insert (invalid) comment into thread "two" with parent from thread 1
        self.app.db.execute(
            [
                "INSERT INTO COMMENTS (tid, parent, created, modified, mode,"
                "   remote_addr, text, author, email, website, voters, notification)",
                "SELECT threads.id, ?, ?, ?, ?, ?,     ?, ?, ?, ?, ?, ?",
                "FROM threads where threads.uri = ?;",
            ],
            (None, 0.0, 0.0, 1, None, "Text", None, None, None, bytes(1), None, "two"),
        )
        # For id=4, the parent has id=1, but is from thread "one". Because id=1
        # does not belong to the current thread "two", it is rejected and id=4
        # chosen instead.
        impossible = self.post("/new?uri=two", data=json.dumps({"text": "...", "parent": 4}))
        self.assertEqual(loads(impossible.data)["parent"], 4)

    def testVerifyFields(self):
        def verify(comment):
            return comments.API.verify(comment)[0]

        # text is missing
        self.assertFalse(verify({}))

        # invalid types
        self.assertFalse(verify({"text": "...", "parent": "xxx"}))
        for key in ("author", "website", "email"):
            self.assertFalse(verify({"text": True, key: 3.14}))

        # value too long
        self.assertTrue(verify({"text": "a" * 65535}))
        self.assertFalse(verify({"text": "a" * 65536}))
        self.assertFalse(verify({"text": "a", "random": "a" * 65536}))

        # text too short and/or blank
        for text in ("", "\n\n\n"):
            self.assertFalse(verify({"text": text}))

        # email/website length
        self.assertTrue(verify({"text": "...", "email": "*" * 254}))
        self.assertTrue(verify({"text": "...", "website": "google.de/" + "a" * 128}))

        self.assertFalse(verify({"text": "...", "email": "*" * 1024}))
        self.assertFalse(verify({"text": "...", "website": "google.de/" + "*" * 1024}))

        # valid website url
        self.assertTrue(comments.isurl("example.tld"))
        self.assertTrue(comments.isurl("http://example.tld"))
        self.assertTrue(comments.isurl("https://example.tld"))
        self.assertTrue(comments.isurl("https://exämple.tld"))
        self.assertTrue(comments.isurl("https://example.tld:1337/"))
        self.assertTrue(comments.isurl("https://example.tld:1337/foobar"))
        self.assertTrue(comments.isurl("https://example.tld:1337/foobar?p=1#isso-thread"))

        self.assertFalse(comments.isurl("ftp://example.tld/"))
        self.assertFalse(comments.isurl("tel:+1234567890"))
        self.assertFalse(comments.isurl("+1234567890"))
        self.assertFalse(comments.isurl("spam"))

    def testGetInvalid(self):
        self.assertEqual(self.get("/?uri=%2Fpath%2F&id=123").status_code, 200)
        data = loads(self.get("/?uri=%2Fpath%2F&id=123").data)
        self.assertEqual(len(data["replies"]), 0)
        self.assertEqual(data["total_replies"], 0)

        self.assertEqual(self.get("/?uri=%2Fpath%2Fspam%2F&id=123").status_code, 200)
        data = loads(self.get("/?uri=%2Fpath%2Fspam%2F&id=123").data)
        self.assertEqual(len(data["replies"]), 0)
        self.assertEqual(data["total_replies"], 0)

        self.assertEqual(self.get("/?uri=?uri=%foo%2F").status_code, 200)
        data = loads(self.get("/?uri=?uri=%foo%2F").data)
        self.assertEqual(len(data["replies"]), 0)
        self.assertEqual(data["total_replies"], 0)

    def testFetchEmpty(self):
        empty = self.get("/?uri=%2Fempty%2F")
        # Empty database returns 200, not 404
        self.assertEqual(empty.status_code, 200)
        data = loads(empty.data)
        self.assertEqual(data["total_replies"], 0)
        self.assertEqual(data["id"], None)

    def testGetLimited(self):
        for i in range(20):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        r = self.get("/?uri=test&limit=10")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 10)
        self.assertEqual(rv["total_replies"], 20)

    def testGetNested(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))

        r = self.get("/?uri=test&parent=1")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 1)
        self.assertEqual(rv["total_replies"], 1)

    def testGetLimitedNested(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        for i in range(20):
            self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))

        r = self.get("/?uri=test&parent=1&limit=10")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 10)
        self.assertEqual(rv["total_replies"], 20)

    def testGetWithOffset(self):
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        r = self.get("/?uri=test&limit=3&offset=2")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual([comment["id"] for comment in rv["replies"]], [3, 4, 5])

    def testGetWithOffsetIgnoredWithoutLimit(self):
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        r = self.get("/?uri=test&offset=2")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual([comment["id"] for comment in rv["replies"]], [1, 2, 3, 4, 5])

    def testGetNestedWithOffset(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))

        r = self.get("/?uri=test&parent=1&limit=3&offset=2")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual([comment["id"] for comment in rv["replies"]], [4, 5, 6])

    def testGetSortedByOldest(self):
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        r = self.get("/?uri=test&sort=oldest")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        # assert order of comments is oldest first
        self.assertEqual([comment["id"] for comment in rv["replies"]], [1, 2, 3, 4, 5])

    def testGetSortedByNewest(self):
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        r = self.get("/?uri=test&sort=newest")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        # assert order of comments is newest first
        self.assertEqual([comment["id"] for comment in rv["replies"]], [5, 4, 3, 2, 1])

    def testGetSortedByUpvotes(self):
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "..."}))

        # update the likes for some comments
        self.app.db.execute("UPDATE comments SET likes = id WHERE id IN (2, 4)")

        r = self.get("/?uri=test&sort=upvotes")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        # assert order of comments is by upvotes
        self.assertEqual([comment["id"] for comment in rv["replies"]], [4, 2, 1, 3, 5])

    def testGetSortedByNewestWithNested(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))

        r = self.get("/?uri=test&sort=newest")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 1)
        # assert order of nested comments is oldest first
        self.assertEqual([comment["id"] for comment in rv["replies"][0]["replies"]], [2, 3, 4, 5, 6])

    def testGetSortedByUpvotesWithNested(self):
        self.post("/new?uri=test", data=json.dumps({"text": "..."}))
        for i in range(5):
            self.post("/new?uri=test", data=json.dumps({"text": "...", "parent": 1}))

        # update the likes for some comments
        self.app.db.execute("UPDATE comments SET likes = id WHERE id IN (3, 6)")

        r = self.get("/?uri=test&sort=upvotes")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(len(rv["replies"]), 1)
        # assert order of nested comments is oldest first
        self.assertEqual([comment["id"] for comment in rv["replies"][0]["replies"]], [2, 3, 4, 5, 6])

    def testUpdate(self):
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        self.put("/id/1", data=json.dumps({"text": "Hello World", "author": "me", "website": "http://example.com/"}))

        r = self.get("/id/1?plain=1")
        self.assertEqual(r.status_code, 200)

        rv = loads(r.data)
        self.assertEqual(rv["text"], "Hello World")
        self.assertEqual(rv["author"], "me")
        self.assertEqual(rv["website"], "http://example.com/")
        self.assertIn("modified", rv)

    def testUpdateWebsiteXSSPayloadIsEscaped(self):
        """Website and author XSS payloads via edit endpoint must be HTML-escaped."""
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        website_payload = "http://x.com/?'onmouseover='alert(document.domain)'x='"
        author_payload = "<script>alert(1)</script>"
        self.put(
            "/id/1",
            data=json.dumps(
                {
                    "text": "Hello World",
                    "author": author_payload,
                    "website": website_payload,
                }
            ),
        )

        rv = loads(self.get("/id/1?plain=1").data)
        self.assertNotIn("'", rv["website"])
        self.assertEqual(
            rv["website"],
            "http://x.com/?&#x27;onmouseover=&#x27;alert(document.domain)&#x27;x=&#x27;",
        )
        self.assertNotIn("<script>", rv["author"])
        self.assertEqual(rv["author"], "&lt;script&gt;alert(1)&lt;/script&gt;")

    def testUpdateForbidden(self):
        self.post("/new?uri=test", data=json.dumps({"text": "Hello world!"}))

        resp = self.put("/id/1", data=json.dumps({}))
        self.assertEqual(resp.status, "400 BAD REQUEST")
        self.assertIn("text is missing", resp.text)

        resp = self.put("/id/1", data=json.dumps({"text": ""}))
        self.assertEqual(resp.status, "400 BAD REQUEST")
        self.assertIn("text is too short", resp.text)

        resp = self.put("/id/1", data=json.dumps({"text": "Hello again!", "website": "name@example.com"}))
        self.assertEqual(resp.status, "400 BAD REQUEST")
        self.assertIn("Website not Django-conform", resp.text)

    def testDelete(self):
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        r = self.delete("/id/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(loads(r.data), None)
        self.assertEqual(self.get("/id/1").status_code, 404)

    def testFetchAuthorization(self):
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        r = self.get("/id/1?plain=1")
        self.assertEqual(r.status_code, 200)

        self.client.delete_cookie(key="1", domain="localhost")
        r = self.get("/id/1?plain=1")
        self.assertEqual(r.status_code, 403)

    def testCookieOfWrongTypeIsRejected(self):
        """The signer is shared with admin session, moderation and unsubscribe
        tokens, so payloads of a foreign shape must be refused, not indexed."""
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        for payload in ({"logged": True}, 1, ["unsubscribe", "bob@example.org"], "nope", []):
            value = self.app.sign(payload)
            self.client.set_cookie("1", value, domain="localhost")

            self.assertEqual(self.get("/id/1?plain=1").status_code, 403)
            self.assertEqual(self.put("/id/1", data=json.dumps({"text": "Hijacked"})).status_code, 403)
            self.assertEqual(self.delete("/id/1").status_code, 403)

    def testEditCookieForMissingCommentIsRejected(self):
        self.client.set_cookie("99", self.app.sign([99, "deadbeef"]), domain="localhost")

        self.assertEqual(self.get("/id/99?plain=1").status_code, 404)
        self.assertEqual(self.put("/id/99", data=json.dumps({"text": "Hijacked"})).status_code, 404)
        self.assertEqual(self.delete("/id/99").status_code, 404)

    def testDeleteWithReference(self):
        client = JSONClient(self.app, Response)
        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "First"}))
        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "First", "parent": 1}))

        r = client.delete("/id/1")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(loads(r.data)["mode"], 4)
        self.assertIn("/path/", self.app.db.threads)

        data = loads(client.get("/?uri=%2Fpath%2F").data)
        self.assertEqual(data["total_replies"], 2)

        self.assertEqual(self.get("/?uri=%2Fpath%2F&id=1").status_code, 200)
        self.assertEqual(self.get("/?uri=%2Fpath%2F&id=2").status_code, 200)

        r = client.delete("/id/2")
        self.assertEqual(self.get("/?uri=%2Fpath%2F").status_code, 200)
        self.assertNotIn("/path/", self.app.db.threads)

        data = loads(client.get("/?uri=%2Fpath%2F").data)
        self.assertEqual(len(data["replies"]), 0)

    def testDeleteWithMultipleReferences(self):
        """
        [ comment 1 ]
            |
            --- [ comment 2, ref 1 ]
            |
            --- [ comment 3, ref 1 ]
        [ comment 4 ]
        """
        client = JSONClient(self.app, Response)

        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "First"}))
        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Second", "parent": 1}))
        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Third", "parent": 1}))
        client.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Last"}))

        client.delete("/id/1")
        self.assertEqual(self.get("/?uri=%2Fpath%2F").status_code, 200)
        client.delete("/id/2")
        self.assertEqual(self.get("/?uri=%2Fpath%2F").status_code, 200)
        client.delete("/id/3")
        self.assertEqual(self.get("/?uri=%2Fpath%2F").status_code, 200)
        client.delete("/id/4")
        self.assertEqual(self.get("/?uri=%2Fpath%2F").status_code, 200)

        data = loads(client.get("/?uri=%2Fpath%2F").data)
        self.assertEqual(len(data["replies"]), 0)

    def testPathVariations(self):
        paths = ["/sub/path/", "/path.html", "/sub/path.html", "path", "/"]

        for path in paths:
            self.assertEqual(self.post("/new?" + urlencode({"uri": path}), data=json.dumps({"text": "..."})).status_code, 201)

        for i, path in enumerate(paths):
            self.assertEqual(self.get("/?" + urlencode({"uri": path})).status_code, 200)
            self.assertEqual(self.get("/id/%i" % (i + 1)).status_code, 200)

    def testDeleteAndCreateByDifferentUsersButSamePostId(self):
        mallory = JSONClient(self.app, Response)
        mallory.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Foo"}))
        mallory.delete("/id/1")

        bob = JSONClient(self.app, Response)
        bob.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Bar"}))

        self.assertEqual(mallory.delete("/id/1").status_code, 403)
        self.assertEqual(bob.delete("/id/1").status_code, 200)

    def testHash(self):
        a = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Aaa"}))
        b = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Bbb"}))
        c = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Ccc", "email": "..."}))

        a = loads(a.data)
        b = loads(b.data)
        c = loads(c.data)

        self.assertNotEqual(a["hash"], "192.168.1.1")
        self.assertEqual(a["hash"], b["hash"])
        self.assertNotEqual(a["hash"], c["hash"])

    def testVisibleFields(self):
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "...", "invalid": "field"}))
        self.assertEqual(rv.status_code, 201)

        rv = loads(rv.data)

        for key in comments.API.FIELDS:
            if key in rv:
                rv.pop(key)

        self.assertListEqual(list(rv.keys()), [])

    def testNoFeed(self):
        rv = self.get("/feed?uri=%2Fpath%2Fnothing")
        self.assertEqual(rv.status_code, 404)

    def testFeedEmpty(self):
        self.conf.set("rss", "base", "https://example.org")

        rv = self.get("/feed?uri=%2Fpath%2Fnothing")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.headers["ETag"], '"empty"')
        data = rv.data.decode("utf-8")
        self.assertEqual(
            data,
            """<?xml version=\'1.0\' encoding=\'utf-8\'?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:thr="http://purl.org/syndication/thread/1.0"><updated>1970-01-01T01:00:00Z</updated><id>tag:example.org,2018:/isso/thread/path/nothing</id><title>Comments for example.org/path/nothing</title></feed>""",
        )

    def testFeed(self):
        self.conf.set("rss", "base", "https://example.org")

        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "First"}))
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "*Second*", "parent": 1}))

        rv = self.get("/feed?uri=%2Fpath%2F")
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.headers["ETag"], '"1-1"')
        data = rv.data.decode("utf-8")
        data = re.sub("[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\\.[0-9]+Z", "2018-04-01T10:00:00Z", data)
        self.maxDiff = None
        # Two accepted outputs, since different versions of Python sort attributes in different order.
        self.assertIn(
            data,
            [
                """<?xml version=\'1.0\' encoding=\'utf-8\'?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:thr="http://purl.org/syndication/thread/1.0"><updated>2018-04-01T10:00:00Z</updated><id>tag:example.org,2018:/isso/thread/path/</id><title>Comments for example.org/path/</title><entry><id>tag:example.org,2018:/isso/1/1</id><title>Comment #1</title><updated>2018-04-01T10:00:00Z</updated><author><name /></author><link href="https://example.org/path/#isso-1" /><content type="html">&lt;p&gt;First&lt;/p&gt;</content></entry><entry><id>tag:example.org,2018:/isso/1/2</id><title>Comment #2</title><updated>2018-04-01T10:00:00Z</updated><author><name /></author><link href="https://example.org/path/#isso-2" /><content type="html">&lt;p&gt;&lt;em&gt;Second&lt;/em&gt;&lt;/p&gt;</content><thr:in-reply-to href="https://example.org/path/#isso-1" ref="tag:example.org,2018:/isso/1/1" /></entry></feed>""",
                """<?xml version=\'1.0\' encoding=\'utf-8\'?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:thr="http://purl.org/syndication/thread/1.0"><updated>2018-04-01T10:00:00Z</updated><id>tag:example.org,2018:/isso/thread/path/</id><title>Comments for example.org/path/</title><entry><id>tag:example.org,2018:/isso/1/1</id><title>Comment #1</title><updated>2018-04-01T10:00:00Z</updated><author><name /></author><link href="https://example.org/path/#isso-1" /><content type="html">&lt;p&gt;First&lt;/p&gt;</content></entry><entry><id>tag:example.org,2018:/isso/1/2</id><title>Comment #2</title><updated>2018-04-01T10:00:00Z</updated><author><name /></author><link href="https://example.org/path/#isso-2" /><content type="html">&lt;p&gt;&lt;em&gt;Second&lt;/em&gt;&lt;/p&gt;</content><thr:in-reply-to ref="tag:example.org,2018:/isso/1/1" href="https://example.org/path/#isso-1" /></entry></feed>""",
            ],
        )

    def testCounts(self):
        rv = self.post("/count", data=json.dumps(["/path/"]))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), [0])

        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "..."}))

        rv = self.post("/count", data=json.dumps(["/path/"]))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), [1])

        for x in range(3):
            self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "..."}))

        rv = self.post("/count", data=json.dumps(["/path/"]))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), [4])

        for x in range(4):
            self.delete("/id/%i" % (x + 1))

        rv = self.post("/count", data=json.dumps(["/path/"]))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), [0])

    def testMultipleCounts(self):
        expected = {"a": 1, "b": 2, "c": 0}

        for uri, count in expected.items():
            for _ in range(count):
                self.post("/new?uri=%s" % uri, data=json.dumps({"text": "..."}))

        rv = self.post("/count", data=json.dumps(list(expected.keys())))
        self.assertEqual(loads(rv.data), list(expected.values()))

    def testModify(self):
        self.post("/new?uri=test", data=json.dumps({"text": "Tpyo"}))

        self.put("/id/1", data=json.dumps({"text": "Tyop"}))
        self.assertEqual(loads(self.get("/id/1").data)["text"], "<p>Tyop</p>")

        self.put("/id/1", data=json.dumps({"text": "Typo"}))
        self.assertEqual(loads(self.get("/id/1").data)["text"], "<p>Typo</p>")

    def testDeleteCommentRemovesThread(self):
        self.client.post("/new?uri=%2F", data=json.dumps({"text": "..."}))
        self.assertIn("/", self.app.db.threads)
        self.client.delete("/id/1")
        self.assertNotIn("/", self.app.db.threads)

    def testCSRF(self):
        js = "application/json"
        form = "application/x-www-form-urlencoded"

        self.post("/new?uri=%2F", data=json.dumps({"text": "..."}))

        # no header is fine (default for XHR)
        self.assertEqual(self.post("/id/1/dislike", content_type="").status_code, 200)

        # x-www-form-urlencoded is definitely not RESTful
        self.assertEqual(self.post("/id/1/dislike", content_type=form).status_code, 403)
        self.assertEqual(self.post("/new?uri=%2F", data=json.dumps({"text": "..."}), content_type=form).status_code, 403)
        # just for the record
        self.assertEqual(self.post("/id/1/dislike", content_type=js).status_code, 200)

    def testPreview(self):
        response = self.post("/preview", data=json.dumps({"text": "This is **mark**_down_"}))
        self.assertEqual(response.status_code, 200)

        rv = loads(response.data)
        self.assertEqual("<p>This is <strong>mark</strong><em>down</em></p>", rv["text"])

    def testTitleNull(self):
        # Thread title set to `null` in API request
        # Javascript `null` equals Python `None`
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Spam", "title": None}))

        thread = self.app.db.threads.get(1)
        # Expect server to attempt to parse uri to extract title
        # utils.parse cannot parse fake /path/, so default="Untitled."
        self.assertEqual(thread.get("title"), "Untitled.")

    def testLatestOk(self):
        # load some comments in a mix of posts
        saved = []
        for idx, post_id in enumerate([1, 2, 2, 1, 2, 1, 3, 1, 4, 2, 3, 4, 1, 2]):
            text = "text-{}".format(idx)
            post_uri = "test-{}".format(post_id)
            self.post("/new?uri=" + post_uri, data=json.dumps({"text": text}))
            saved.append((post_uri, text))

        response = self.get("/latest?limit=5")
        self.assertEqual(response.status_code, 200)

        body = loads(response.data)
        expected_items = saved[-5:]  # latest 5
        for reply, expected in zip(body, expected_items):
            expected_uri, expected_text = expected
            self.assertIn(expected_text, reply["text"])
            self.assertEqual(expected_uri, reply["uri"])

    def testLatestWithoutLimit(self):
        response = self.get("/latest")
        self.assertEqual(response.status_code, 400)

    def testLatestBadLimitNaN(self):
        response = self.get("/latest?limit=WAT")
        self.assertEqual(response.status_code, 400)

    def testLatestBadLimitNegative(self):
        response = self.get("/latest?limit=-12")
        self.assertEqual(response.status_code, 400)

    def testLatestBadLimitZero(self):
        response = self.get("/latest?limit=0")
        self.assertEqual(response.status_code, 400)

    def testLatestNotEnabled(self):
        # disable the endpoint
        self.conf.set("general", "latest-enabled", "false")

        response = self.get("/latest?limit=5")
        self.assertEqual(response.status_code, 404)

    def testFetchAddsNoCacheHeaders(self):
        """Test that fetch endpoint adds no-cache headers by default."""
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        r = self.get("/?uri=%2Fpath%2F")

        self.assertEqual(r.status_code, 200)
        for header, value in NO_CACHE_HEADERS.items():
            self.assertIn(header, r.headers)
            self.assertEqual(r.headers[header], value)

    def testViewAddsNoCacheHeaders(self):
        """Test that view endpoint adds no-cache headers by default."""
        self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))
        r = self.get("/id/1")

        self.assertEqual(r.status_code, 200)
        for header, value in NO_CACHE_HEADERS.items():
            self.assertIn(header, r.headers)
            self.assertEqual(r.headers[header], value)


class TestHostDependent(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        self.conf = conf

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)

        self.client = JSONClient(self.app, Response)
        self.post = self.client.post

    def tearDown(self):
        os.unlink(self.path)

    def testSecureCookieNoConf(self):
        self.app.wsgi_app = FakeHost(self.app.wsgi_app, "isso-dev.local", "https")
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        self.assertIn("Secure", rv.headers["Set-Cookie"])
        self.assertIn("Secure", rv.headers["X-Set-Cookie"])
        self.assertIn("SameSite=None", rv.headers["Set-Cookie"])

    def testInSecureCookieNoConf(self):
        self.app.wsgi_app = FakeHost(self.app.wsgi_app, "isso-dev.local", "http")
        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        self.assertNotIn("Secure", rv.headers["Set-Cookie"])
        self.assertNotIn("Secure", rv.headers["X-Set-Cookie"])
        self.assertIn("SameSite=Lax", rv.headers["Set-Cookie"])

    def testSameSiteConfNone(self):
        # By default, isso should set SameSite=Lax when served over http
        self.app.wsgi_app = FakeHost(self.app.wsgi_app, "isso-dev.local", "http")
        # Conf overrides SameSite setting
        self.conf.set("server", "samesite", "None")

        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        self.assertNotIn("Secure", rv.headers["Set-Cookie"])
        self.assertNotIn("Secure", rv.headers["X-Set-Cookie"])
        self.assertIn("SameSite=None", rv.headers["Set-Cookie"])

    def testSameSiteConfLax(self):
        # By default, isso should set SameSite=None when served over https
        self.app.wsgi_app = FakeHost(self.app.wsgi_app, "isso-dev.local", "https")
        # Conf overrides SameSite setting
        self.conf.set("server", "samesite", "Lax")

        rv = self.post("/new?uri=%2Fpath%2F", data=json.dumps({"text": "Lorem ipsum ..."}))

        self.assertIn("Secure", rv.headers["Set-Cookie"])
        self.assertIn("Secure", rv.headers["X-Set-Cookie"])
        self.assertIn("SameSite=Lax", rv.headers["Set-Cookie"])


class TestModeratedComments(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def tearDown(self):
        os.unlink(self.path)

    def testAddComment(self):
        rv = self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.assertEqual(rv.status_code, 202)

        self.assertEqual(self.client.get("/id/1").status_code, 200)
        self.assertEqual(self.client.get("/?uri=test").status_code, 200)

        data = loads(self.client.get("/?uri=test").data)
        self.assertEqual(len(data["replies"]), 0)

        self.app.db.comments.activate(1)
        self.assertEqual(self.client.get("/?uri=test").status_code, 200)

    def testViewRejectsCookieIssuedForOtherComment(self):
        """A cookie for one's own comment must not unlock a pending one."""
        bob = JSONClient(self.app, Response)
        bob.post("/new?uri=test", data=json.dumps({"text": "Bob's pending comment"}))

        mallory = JSONClient(self.app, Response)
        mallory.post("/new?uri=test", data=json.dumps({"text": "Mallory's comment"}))

        cookie = mallory.get_cookie("2", domain="localhost").value
        mallory.set_cookie("1", cookie, domain="localhost")

        self.assertEqual(mallory.get("/id/1?plain=1").status_code, 403)

    def testModerateComment(self):
        id_ = 1
        signed = self.app.sign(id_)

        # Create new comment, should have mode=2 (pending moderation)
        rv = self.client.post("/new?uri=/moderated", data=json.dumps({"text": "..."}))
        self.assertEqual(rv.status_code, 202)
        self.assertEqual(self.client.get("/id/1").status_code, 200)
        self.assertEqual(self.app.db.comments.get(id_)["mode"], 2)
        self.assertEqual(self.app.db.comments.get(id_)["text"], "...")

        # GET should return some html form
        action = "activate"
        rv_activate_get = self.client.get("/id/%d/%s/%s" % (id_, action, signed))
        self.assertEqual(rv_activate_get.status_code, 200)
        self.assertIn(b"Activate: Are you sure?", rv_activate_get.data)
        self.assertIn(b"http://invalid.local/moderated#isso-1", rv_activate_get.data)

        # Activate comment
        action = "activate"
        rv_activated = self.client.post("/id/%d/%s/%s" % (id_, action, signed))
        self.assertEqual(rv_activated.status_code, 200)
        # JSON serializes integer keys as strings; 1 comment now in mode=1
        self.assertEqual(loads(rv_activated.data)["counts"], {"1": 1})

        # Activating should be idempotent
        rv_activated = self.client.post("/id/%d/%s/%s" % (id_, action, signed))
        self.assertEqual(rv_activated.status_code, 200)
        self.assertEqual(loads(rv_activated.data)["counts"], {"1": 1})

        # Comment should have mode=1 (activated)
        self.assertEqual(self.app.db.comments.get(id_)["mode"], 1)

        # Edit comment
        action = "edit"
        rv_edit = self.client.post("/id/%d/%s/%s" % (id_, action, signed), data=json.dumps({"text": "new text"}))
        self.assertEqual(rv_edit.status_code, 200)
        self.assertEqual(json.loads(rv_edit.data)["id"], id_)
        self.assertEqual(self.app.db.comments.get(id_)["text"], "new text")

        # Wrong action on comment is handled by the routing
        action = "foo"
        rv_wrong_action = self.client.post("/id/%d/%s/%s" % (id_, action, signed))
        self.assertEqual(rv_wrong_action.status_code, 404)

        # Delete comment
        action = "delete"
        rv_deleted = self.client.post("/id/%d/%s/%s" % (id_, action, signed))
        self.assertEqual(rv_deleted.status_code, 200)
        # comment fully deleted (no references), so all mode counts are empty
        self.assertEqual(loads(rv_deleted.data)["counts"], {})

        # Comment should no longer exist
        self.assertEqual(self.app.db.comments.get(id_), None)

    def testModerateEditXSSPayloadIsEscaped(self):
        """XSS payloads in author/website via moderate edit endpoint must be HTML-escaped."""
        id_ = 1
        signed = self.app.sign(id_)

        self.client.post("/new?uri=/moderated", data=json.dumps({"text": "..."}))

        website_payload = "http://x.com/?'onmouseover='alert(document.domain)'x='"
        author_payload = "<script>alert(1)</script>"
        rv = self.client.post(
            "/id/%d/edit/%s" % (id_, signed),
            data=json.dumps(
                {
                    "text": "new text",
                    "author": author_payload,
                    "website": website_payload,
                }
            ),
        )
        self.assertEqual(rv.status_code, 200)

        stored = self.app.db.comments.get(id_)
        self.assertNotIn("'", stored["website"])
        self.assertEqual(
            stored["website"],
            "http://x.com/?&#x27;onmouseover=&#x27;alert(document.domain)&#x27;x=&#x27;",
        )
        self.assertNotIn("<script>", stored["author"])
        self.assertEqual(stored["author"], "&lt;script&gt;alert(1)&lt;/script&gt;")

    def testModerateRejectsOtherSignedPayloads(self):
        """The signer is shared: only a bare comment id is a moderation key."""
        self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))

        payloads = [("verify", 1), ("unsubscribe", "a@example.org"), [1, "checksum"], {"logged": True}, True]
        for payload in payloads:
            key = self.app.sign(payload)
            for action in ("activate", "edit", "delete"):
                with self.subTest(payload=payload, action=action):
                    self.assertEqual(self.client.get("/id/1/%s/%s" % (action, key)).status_code, 403)
                    self.assertEqual(self.client.post("/id/1/%s/%s" % (action, key)).status_code, 403)

        self.assertEqual(self.app.db.comments.get(1)["mode"], 2)


class TestUnsubscribe(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

        # add default comment
        rv = self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.assertEqual(rv.status_code, 202)

    def tearDown(self):
        os.unlink(self.path)

    def testUnsubscribe(self):
        id_ = 1
        email = "test@test.example"
        key = self.app.sign(("unsubscribe", email))

        # GET should return some html form
        rv_unsubscribe_get = self.client.get("/id/%d/unsubscribe/%s/%s" % (id_, email, key))
        self.assertEqual(rv_unsubscribe_get.status_code, 200)
        self.assertIn(b"Successfully unsubscribed", rv_unsubscribe_get.data)

        # Incomplete key should fail
        key = self.app.sign(["unsubscribe"])
        rv_incomplete_key = self.client.get("/id/%d/unsubscribe/%s/%s" % (id_, email, key))
        self.assertEqual(rv_incomplete_key.status_code, 403)

        # Wrong key type should fail
        key = self.app.sign(1)
        rv_wrong_key_type = self.client.get("/id/%d/unsubscribe/%s/%s" % (id_, email, key))
        self.assertEqual(rv_wrong_key_type.status_code, 403)


class TestPurgeComments(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(config.default_file())
        conf.set("general", "dbpath", self.path)
        conf.set("moderation", "enabled", "true")
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def testPurgeDoesNoHarm(self):
        self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.app.db.comments.activate(1)
        self.app.db.comments.purge(0)
        self.assertEqual(self.client.get("/?uri=test").status_code, 200)

    def testPurgeWorks(self):
        self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(0)
        self.assertEqual(self.client.get("/id/1").status_code, 404)

        self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        self.app.db.comments.purge(3600)
        self.assertEqual(self.client.get("/id/1").status_code, 200)

    def _post_comment(self, mode, age):
        rv = self.client.post("/new?uri=test", data=json.dumps({"text": "..."}))
        id_ = loads(rv.data)["id"]
        self.app.db.comments.update(id_, {"mode": mode, "created": time.time() - age})
        return id_

    def testPurgeUnverifiedAfterLinkExpires(self):
        expired = self._post_comment(8, VERIFICATION_LINK_MAX_AGE + 60)
        fresh = self._post_comment(8, VERIFICATION_LINK_MAX_AGE - 60)
        pending = self._post_comment(2, VERIFICATION_LINK_MAX_AGE + 60)

        self.app.db.comments.purge(30 * 24 * 3600)

        self.assertIsNone(self.app.db.comments.get(expired))
        self.assertIsNotNone(self.app.db.comments.get(fresh))
        self.assertIsNotNone(self.app.db.comments.get(pending))

    def testPurgeKeepsUnverifiedYoungerThanLinkAge(self):
        fresh = self._post_comment(8, 60)
        pending = self._post_comment(2, 60)

        self.app.db.comments.purge(0)

        self.assertIsNotNone(self.app.db.comments.get(fresh))
        self.assertIsNone(self.app.db.comments.get(pending))

    def testActivateUnverified(self):
        id_ = self._post_comment(8, 0)
        self.app.db.comments.activate(id_)
        self.assertEqual(self.app.db.comments.get(id_)["mode"], 1)


class TestPurgeJob(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        self.addCleanup(os.unlink, self.path)
        self.conf = config.load(config.default_file())
        self.conf.set("general", "dbpath", self.path)
        self.conf.set("moderation", "purge-after", "30d")

        smtp_connection = mock.patch("isso.ext.notifications.SMTPConnection")
        smtp_connection.start()
        self.addCleanup(smtp_connection.stop)

    def _add_comment(self, mode, age):
        database = SQLite3(self.path, self.conf)
        database.threads.new("/", None)
        comment = {"mode": mode, "remote_addr": "127.0.0.1", "text": "...", "created": time.time() - age}
        return database.comments.add("/", comment)["id"]

    def _run_purge_job_once(self):
        """Start a threaded app and run one pass of its purge job in this
        thread. Return the sleep intervals (empty if no job was started)."""

        class StopPurgeJob(Exception):
            pass

        sleeps = []

        def sleep(seconds):
            sleeps.append(seconds)
            raise StopPurgeJob

        def start_new_thread(function, args, kwargs):
            with self.assertRaises(StopPurgeJob):
                function(*args, **kwargs)

        class App(Isso, core.ThreadedMixin):
            pass

        with (
            mock.patch.object(core.thread, "start_new_thread", start_new_thread),
            mock.patch.object(core.time, "sleep", sleep),
        ):
            self.app = App(self.conf)
        return sleeps

    def testEmailVerificationAloneStartsHourlyPurge(self):
        self.conf.set("moderation", "require-email-verification", "true")
        expired = self._add_comment(mode=8, age=VERIFICATION_LINK_MAX_AGE + 60)

        self.assertEqual(self._run_purge_job_once(), [3600])
        self.assertIsNone(self.app.db.comments.get(expired))

    def testEmailVerificationKeepsShorterPurgeAfter(self):
        self.conf.set("moderation", "require-email-verification", "true")
        self.conf.set("moderation", "purge-after", "10m")

        self.assertEqual(self._run_purge_job_once(), [600])

    def testModerationAlonePurgesEveryPurgeAfter(self):
        self.conf.set("moderation", "enabled", "true")

        self.assertEqual(self._run_purge_job_once(), [30 * 24 * 3600])

    def testNoPurgeJobWithoutModerationOrEmailVerification(self):
        self.assertEqual(self._run_purge_job_once(), [])


class TestEmailVerification(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        self.conf = config.load(config.default_file())
        self.conf.set("general", "dbpath", self.path)
        self.conf.set("general", "latest-enabled", "true")
        self.conf.set("moderation", "require-email-verification", "true")
        self.conf.set("guard", "enabled", "off")
        self.conf.set("hash", "algorithm", "none")
        self.conf.set("rss", "base", "https://example.org")
        self.conf.set("smtp", "to", "admin@example.org")

        # Send mail at once, to a fake SMTP server.
        smtp_connection = mock.patch("isso.ext.notifications.SMTPConnection")
        self.smtp_connection = smtp_connection.start()
        self.addCleanup(smtp_connection.stop)
        start_new_thread = mock.patch("isso.ext.notifications.start_new_thread", lambda function, args: function(*args))
        start_new_thread.start()
        self.addCleanup(start_new_thread.stop)

        self._start_app()

    def tearDown(self):
        os.unlink(self.path)

    def _start_app(self):
        class App(Isso, core.Mixin):
            pass

        self.app = App(self.conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
        self.client = JSONClient(self.app, Response)

    def _post(self, email, **extra):
        return self.client.post("/new?uri=test", data=json.dumps({"text": "...", "email": email, **extra}))

    def _verify_url(self, id_, key=None):
        return "/id/%d/verify/%s" % (id_, key or self.app.sign(("verify", id_)))

    def _verify_key_signed_ago(self, id_, age):
        with mock.patch.object(TimestampSigner, "get_timestamp", return_value=int(time.time()) - age):
            return self.app.sign(("verify", id_))

    def _record_verified(self):
        verified = []
        self.app.signal.subscriptions["comments.verified"].append(lambda thread, comment: verified.append(comment))
        return verified

    def _sent_mails(self):
        """Return the mails sent since the last call, as (to, subject, body) tuples."""
        send_message = self.smtp_connection.return_value.__enter__.return_value.send_message
        mails = [(msg["To"], msg["Subject"], msg.get_content()) for (msg, _, _), _ in send_message.call_args_list]
        send_message.reset_mock()
        return mails

    def testNewCommentIsUnverified(self):
        rv = self._post("bob@example.org")
        self.assertEqual(rv.status_code, 202)
        self.assertEqual(loads(rv.data)["mode"], 8)
        self.assertEqual(self.app.db.comments.get(1)["mode"], 8)

    def testEmailRequiredWithGuardOff(self):
        for email in (None, ""):
            rv = self._post(email)
            self.assertEqual(rv.status_code, 403)
            self.assertEqual(loads(rv.data)["reason"], "require-email")

        self.assertEqual(self.app.db.comments.count_modes(), {})

    def testOnePendingConfirmationPerEmailPerHour(self):
        self.assertEqual(self._post("bob@example.org").status_code, 202)

        rv = self._post("bob@example.org")
        self.assertEqual(rv.status_code, 429)
        self.assertEqual(loads(rv.data)["reason"], "verification-pending")
        self.assertEqual(self.app.db.comments.count_modes(), {8: 1})
        self.assertEqual([to for to, _, _ in self._sent_mails()], ["bob@example.org"])

        self.assertEqual(self._post("alice@example.org").status_code, 202)

        self.app.db.execute("UPDATE comments SET created=? WHERE id=1", (time.time() - VERIFICATION_RATE_WINDOW - 60,))
        self.assertEqual(self._post("bob@example.org").status_code, 202)

    def testUnverifiedCommentsAreHidden(self):
        self._post("published@example.org")
        self.app.db.comments.activate(1)
        self._post("top@example.org")
        self._post("reply@example.org", parent=1)

        data = loads(self.client.get("/?uri=test").data)
        self.assertEqual([c["id"] for c in data["replies"]], [1])
        self.assertEqual(data["replies"][0]["total_replies"], 0)

        self.assertEqual(loads(self.client.post("/count", data=json.dumps(["test"])).data), [1])
        self.assertEqual(self.client.get("/feed?uri=test").headers["ETag"], '"1-1"')
        self.assertEqual([c["id"] for c in loads(self.client.get("/latest?limit=5").data)], [1])

    def testConfigRequiresEmail(self):
        self.assertFalse(self.conf.getboolean("guard", "require-email"))
        self.assertTrue(loads(self.client.get("/config").data)["config"]["require-email"])

    def testPreviouslyApprovedEmailStillNeedsConfirmation(self):
        self.conf.set("moderation", "enabled", "true")
        self.conf.set("moderation", "approve-if-email-previously-approved", "true")
        self._start_app()

        self._post("bob@example.org")
        self.app.db.comments.activate(1)

        rv = self._post("bob@example.org")
        self.assertEqual(rv.status_code, 202)
        self.assertEqual(self.app.db.comments.get(2)["mode"], 8)

    def testVerifyGetChangesNothing(self):
        self._post("bob@example.org")
        verified = self._record_verified()

        rv = self.client.get(self._verify_url(1))
        self.assertEqual(rv.status_code, 200)
        self.assertIn(b"confirm(", rv.data)
        self.assertEqual(self.app.db.comments.get(1)["mode"], 8)
        self.assertEqual(verified, [])

    def testVerifyPublishesComment(self):
        self._post("bob@example.org")
        verified = self._record_verified()

        rv = self.client.post(self._verify_url(1))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), {"id": 1, "mode": 1})
        self.assertEqual([(c["id"], c["mode"]) for c in verified], [(1, 1)])
        self.assertEqual([c["id"] for c in loads(self.client.get("/?uri=test").data)["replies"]], [1])

    def testVerifyTwiceChangesNothing(self):
        self._post("bob@example.org")
        verified = self._record_verified()
        self.client.post(self._verify_url(1))

        rv = self.client.post(self._verify_url(1))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(loads(rv.data), {"id": 1, "mode": 1})
        self.assertEqual(len(verified), 1)
        self.assertEqual(self.client.get(self._verify_url(1)).status_code, 200)

    def testVerifyWithModeration(self):
        self.conf.set("moderation", "enabled", "true")
        self.conf.set("moderation", "approve-if-email-previously-approved", "true")
        self._start_app()

        self._post("bob@example.org")
        self.assertEqual(loads(self.client.post(self._verify_url(1)).data)["mode"], 2)
        self.assertEqual(self.app.db.comments.get(1)["mode"], 2)
        self.app.db.comments.activate(1)

        # The auto-approve check runs at confirmation.
        self._post("bob@example.org")
        self.assertEqual(loads(self.client.post(self._verify_url(2)).data)["mode"], 1)
        self.assertEqual(self.app.db.comments.get(2)["mode"], 1)

        self._post("alice@example.org")
        self.assertEqual(loads(self.client.post(self._verify_url(3)).data)["mode"], 2)

    def testVerifyKeyLastsTwoDays(self):
        self._post("bob@example.org")
        key = self._verify_key_signed_ago(1, VERIFICATION_LINK_MAX_AGE - 60)

        self.assertEqual(self.client.post(self._verify_url(1, key)).status_code, 200)

    def testVerifyRejectsInvalidKeys(self):
        self._post("bob@example.org")
        self._post("alice@example.org")
        expired = self._verify_key_signed_ago(1, VERIFICATION_LINK_MAX_AGE + 60)

        urls = {
            "expired": self._verify_url(1, expired),
            "bad signature": self._verify_url(1, URLSafeTimedSerializer("not the session key").dumps(("verify", 1))),
            "not a key": self._verify_url(1, "invalid"),
            "wrong tag": self._verify_url(1, self.app.sign(("unsubscribe", 1))),
            "key of other comment": self._verify_url(1, self.app.sign(("verify", 2))),
            "moderation key": self._verify_url(1, self.app.sign(1)),
            "no such comment": self._verify_url(99),
        }
        for name, url in urls.items():
            for method in (self.client.get, self.client.post):
                with self.subTest(name, method=method.__name__):
                    rv = method(url)
                    self.assertEqual(rv.status_code, 403)
                    self.assertIn(comments.API.VERIFY_LINK_FAILED.encode(), rv.data)

        self.assertEqual(self.app.db.comments.count_modes(), {8: 2})

    def testNewerCommentReplacesOldKey(self):
        self._post("bob@example.org")
        self.app.db.execute("UPDATE comments SET created=? WHERE id=1", (time.time() - VERIFICATION_RATE_WINDOW - 60,))
        self.assertEqual(self._post("bob@example.org").status_code, 202)

        self.assertEqual(self.client.get(self._verify_url(1)).status_code, 403)
        self.assertEqual(self.client.post(self._verify_url(1)).status_code, 403)
        self.assertEqual(self.client.post(self._verify_url(2)).status_code, 200)
        self.assertEqual(self.client.post(self._verify_url(1)).status_code, 403)
        self.assertEqual(self.app.db.comments.get(1)["mode"], 8)

    def testConfirmedEmailCanPostAgain(self):
        self._post("bob@example.org")
        self.client.post(self._verify_url(1))

        self.assertEqual(self._post("bob@example.org").status_code, 202)

    def testConfirmPageEscapesThreadUri(self):
        uri = "/</script><script>alert(1)</script>"
        self.client.post(
            "/new?" + urlencode({"uri": uri}),
            data=json.dumps({"text": "...", "email": "bob@example.org", "title": "Title"}),
        )

        rv = self.client.get(self._verify_url(1))
        self.assertEqual(rv.status_code, 200)
        self.assertNotIn(b"<script>alert(1)", rv.data)
        link = re.search(rb'window\.location\.href = ("[^"]*");', rv.data).group(1)
        self.assertEqual(json.loads(link), "http://invalid.local" + uri + "#isso-1")

    def testConfirmationEmail(self):
        self.conf.set("server", "public-endpoint", "https://comments.example.org")
        self._start_app()
        self.client.post(
            "/new?uri=%2Fthread-uri",
            data=json.dumps({"text": "Comment text", "email": "bob@example.org", "title": "Thread title"}),
        )

        [(to, subject, body)] = self._sent_mails()
        self.assertEqual(to, "bob@example.org")
        self.assertEqual(subject, "Confirm your comment on http://invalid.local")
        for chosen_by_client in ("Comment text", "Thread title", "thread-uri"):
            self.assertNotIn(chosen_by_client, body)

        link = re.search(r"^https://comments\.example\.org(/id/1/verify/\S+)$", body, re.MULTILINE)
        self.assertIsNotNone(link)
        self.assertEqual(loads(self.client.post(link.group(1)).data), {"id": 1, "mode": 1})

    def testAdminAndReplyEmailsWaitForConfirmation(self):
        self.conf.set("general", "notify", "smtp")
        self.conf.set("general", "reply-notifications", "true")
        self._start_app()
        self._post("alice@example.org", notification=1)
        self.client.post(self._verify_url(1))
        self._sent_mails()

        self._post("bob@example.org", parent=1)
        self.assertEqual([to for to, _, _ in self._sent_mails()], ["bob@example.org"])

        self.client.post(self._verify_url(2))
        self.assertEqual(sorted(to for to, _, _ in self._sent_mails()), ["admin@example.org", "alice@example.org"])

    def testReplyToUnverifiedCommentDoesNotEmailParent(self):
        self.conf.set("general", "reply-notifications", "true")
        self._start_app()
        self._post("victim@example.org", notification=1)
        self._post("attacker@example.org", parent=1)
        self._sent_mails()

        self.client.post(self._verify_url(2))
        self.assertEqual(self._sent_mails(), [])
