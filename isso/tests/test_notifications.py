# -*- encoding: utf-8 -*-

import hashlib
import hmac
import json
import unittest

from isso import config
from isso.ext import notifications


class TestWebhook(unittest.TestCase):
    def test_new_comment_posts_signed_payload(self):
        webhook = notifications.Webhook(
            type(
                "Isso",
                (),
                {
                    "conf": config.new(
                        {
                            "webhook": {
                                "url": """
                                    https://hooks.example.test/first
                                    https://hooks.example.test/second
                                """,
                                "secret": "test-secret",
                                "timeout": "5",
                            }
                        }
                    )
                },
            )()
        )
        dispatched = []
        requests = []

        def fake_start_new_thread(function, args):
            dispatched.append((function, args))

        def fake_urlopen(request, timeout):
            requests.append((request, timeout))

            class Response(object):
                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    pass

            return Response()

        original_start_new_thread = notifications.start_new_thread
        original_urlopen = notifications.urlopen
        notifications.start_new_thread = fake_start_new_thread
        notifications.urlopen = fake_urlopen
        try:
            webhook.notify_new(
                {"id": 1, "uri": "/post", "title": "A post"},
                {
                    "id": 2,
                    "parent": None,
                    "created": 1.0,
                    "modified": None,
                    "mode": 1,
                    "text": "Hello",
                    "author": "Alice",
                    "website": "https://example.test",
                    "email": "alice@example.test",
                    "remote_addr": "192.0.2.1",
                    "voters": b"private",
                },
            )

            self.assertEqual(len(dispatched), 1)
            function, args = dispatched[0]
            function(*args)
        finally:
            notifications.start_new_thread = original_start_new_thread
            notifications.urlopen = original_urlopen

        self.assertEqual(len(requests), 2)
        request, timeout = requests[0]
        body = request.data
        payload = json.loads(body.decode("utf-8"))

        self.assertEqual(
            [request.full_url for request, timeout in requests],
            ["https://hooks.example.test/first", "https://hooks.example.test/second"],
        )
        self.assertEqual(request.get_method(), "POST")
        self.assertEqual(request.get_header("Content-type"), "application/json")
        self.assertEqual(request.get_header("X-isso-event"), "comment.created")
        self.assertEqual(
            request.get_header("X-isso-signature"),
            "sha256=" + hmac.new(b"test-secret", body, hashlib.sha256).hexdigest(),
        )
        self.assertEqual(timeout, 5)
        self.assertEqual(payload["thread"], {"id": 1, "uri": "/post", "title": "A post"})
        self.assertEqual(payload["comment"]["id"], 2)
        self.assertNotIn("email", payload["comment"])
        self.assertNotIn("remote_addr", payload["comment"])
        self.assertNotIn("voters", payload["comment"])
