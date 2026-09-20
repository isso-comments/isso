# -*- encoding: utf-8 -*-

import hashlib
import hmac
import json
import unittest

from isso import config, local
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


class FakeComments(object):
    def __init__(self, rows):
        self.rows = rows

    def get(self, id):
        for row in self.rows:
            if row["id"] == id:
                return row
        return None

    def fetch(self, uri, mode=5, parent="any", **kwargs):
        for row in self.rows:
            if parent != "any" and row["parent"] != parent:
                continue
            yield row

    def thread_subscribers(self, tid):
        return [row for row in self.rows if row["notification"] == 2]


def comment(id, parent=None, email=None, notification=0, mode=1):
    return {
        "id": id,
        "parent": parent,
        "mode": mode,
        "text": "Comment %i" % id,
        "author": "Author %i" % id,
        "website": None,
        "email": email,
        "remote_addr": "192.0.2.1",
        "notification": notification,
    }


class TestSMTPNotifyUsers(unittest.TestCase):
    """Who gets an email for a new comment, and with which subject."""

    def setUp(self):
        local.origin = "https://example.test"

    def smtp(self, rows, reply_notify=True, thread_notify=True):
        smtp = notifications.SMTP.__new__(notifications.SMTP)
        smtp.isso = type(
            "Isso",
            (),
            {
                "db": type("DB", (), {"comments": FakeComments(rows)})(),
                # tell the two unsubscribe scopes apart in the generated links
                "sign": staticmethod(lambda payload: "thread-key" if len(payload) == 3 else "reply-key"),
            },
        )()
        smtp.public_endpoint = "https://comments.example.test"
        smtp.reply_notify = reply_notify
        smtp.thread_notify = thread_notify

        self.sent = []

        def sendmail(subject, body, thread, comment, to=None, headers=None):
            self.sent.append({"subject": subject, "body": body, "to": to, "headers": headers})

        smtp.sendmail = sendmail
        return smtp

    thread = {"id": 1, "uri": "/post", "title": "A post"}

    def test_thread_subscriber_notified_about_top_level_comment(self):
        subscriber = comment(1, email="alice@example.test", notification=2)
        new = comment(2, email="bob@example.test")
        smtp = self.smtp([subscriber, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual([mail["to"] for mail in self.sent], ["alice@example.test"])
        self.assertEqual(self.sent[0]["subject"], "New comment posted on A post")
        # thread-wide unsubscribe link pointing at the subscriber's own comment
        url = "https://comments.example.test/id/1/unsubscribe/alice%40example.test/thread-key"
        self.assertIn(url, self.sent[0]["body"])
        self.assertEqual(self.sent[0]["headers"], (("List-Unsubscribe", url),))

    def test_reply_subscriber_not_notified_about_unrelated_comment(self):
        subscriber = comment(1, email="alice@example.test", notification=1)
        new = comment(2, email="bob@example.test")
        smtp = self.smtp([subscriber, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual(self.sent, [])

    def test_reply_subscriber_notified_about_reply(self):
        subscriber = comment(1, email="alice@example.test", notification=1)
        new = comment(2, parent=1, email="bob@example.test")
        smtp = self.smtp([subscriber, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual([mail["to"] for mail in self.sent], ["alice@example.test"])
        self.assertEqual(self.sent[0]["subject"], "Re: New comment posted on A post")
        # unchanged reply-scoped unsubscribe link pointing at the parent
        url = "https://comments.example.test/id/1/unsubscribe/alice%40example.test/reply-key"
        self.assertIn(url, self.sent[0]["body"])
        self.assertEqual(self.sent[0]["headers"], (("List-Unsubscribe", url),))

    def test_sibling_reply_subscriber_link_points_at_parent(self):
        parent = comment(1, email="carol@example.test")
        subscriber = comment(2, parent=1, email="alice@example.test", notification=1)
        new = comment(3, parent=1, email="bob@example.test")
        smtp = self.smtp([parent, subscriber, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual([mail["to"] for mail in self.sent], ["alice@example.test"])
        self.assertIn("/id/1/unsubscribe/alice%40example.test/reply-key", self.sent[0]["body"])

    def test_subscriber_notified_once_per_email(self):
        first = comment(1, email="alice@example.test", notification=2)
        second = comment(2, parent=1, email="alice@example.test", notification=2)
        new = comment(3, parent=1, email="bob@example.test")
        smtp = self.smtp([first, second, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual([mail["to"] for mail in self.sent], ["alice@example.test"])
        self.assertEqual(self.sent[0]["subject"], "Re: New comment posted on A post")

    def test_thread_subscriber_gets_thread_link_for_reply(self):
        subscriber = comment(1, email="alice@example.test", notification=2)
        new = comment(2, parent=1, email="bob@example.test")
        smtp = self.smtp([subscriber, new])

        smtp.notify_users(self.thread, new)

        self.assertEqual([mail["to"] for mail in self.sent], ["alice@example.test"])
        self.assertEqual(self.sent[0]["subject"], "Re: New comment posted on A post")
        # a reply-scoped link would silently cancel the thread subscription too
        url = "https://comments.example.test/id/1/unsubscribe/alice%40example.test/thread-key"
        self.assertEqual(self.sent[0]["headers"], (("List-Unsubscribe", url),))

    def test_reply_link_when_thread_notifications_disabled(self):
        subscriber = comment(1, email="alice@example.test", notification=2)
        new = comment(2, parent=1, email="bob@example.test")
        smtp = self.smtp([subscriber, new], thread_notify=False)

        smtp.notify_users(self.thread, new)

        url = "https://comments.example.test/id/1/unsubscribe/alice%40example.test/reply-key"
        self.assertEqual(self.sent[0]["headers"], (("List-Unsubscribe", url),))

    def test_author_not_notified_about_own_comment(self):
        new = comment(1, email="alice@example.test", notification=2)
        smtp = self.smtp([new])

        smtp.notify_users(self.thread, new)

        self.assertEqual(self.sent, [])

    def test_thread_notifications_disabled(self):
        subscriber = comment(1, email="alice@example.test", notification=2)
        new = comment(2, email="bob@example.test")
        smtp = self.smtp([subscriber, new], thread_notify=False)

        smtp.notify_users(self.thread, new)

        self.assertEqual(self.sent, [])
