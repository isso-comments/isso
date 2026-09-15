# -*- encoding: utf-8 -*-

import time
from configparser import NoOptionError, NoSectionError


class Guard:
    def __init__(self, db):
        self.db = db
        self.conf = db.conf.section("guard")
        try:
            self.max_age = db.conf.getint("general", "max-age")
        except (NoOptionError, NoSectionError):
            self.max_age = None

    def validate(self, uri, comment):
        """Return a ``(valid, reason, message)`` tuple.

        ``reason`` is a short machine-readable code for the client, and
        ``message`` is a human-readable description for logs and extensions.

        ``reason`` values (``"ratelimit"``, ``"direct-reply"``,
        ``"reply-to-self"``, ``"require-email"``, ``"require-author"``) are a
        contract with the JS client: ``isso/js/app/isso.js`` builds an i18n
        key as ``"guard-" + reason``.
        """
        if not self.conf.getboolean("enabled"):
            return True, "", ""

        for func in (self._limit, self._spam):
            valid, reason, message = func(uri, comment)
            if not valid:
                return False, reason, message
        return True, "", ""

    @classmethod
    def ids(cls, rv):
        return [str(col[0]) for col in rv]

    def _limit(self, uri, comment):
        # block more than :param:`ratelimit` comments per minute
        rv = self.db.execute(
            ["SELECT id FROM comments WHERE remote_addr = ? AND ? - created < 60;"], (comment["remote_addr"], time.time())
        ).fetchall()

        if len(rv) >= self.conf.getint("ratelimit"):
            return (
                False,
                "ratelimit",
                "{0}: ratelimit exceeded ({1})".format(comment["remote_addr"], ", ".join(Guard.ids(rv))),
            )

        # block more than three comments as direct response to the post
        if comment["parent"] is None:
            rv = self.db.execute(
                [
                    "SELECT id FROM comments WHERE",
                    "    tid = (SELECT id FROM threads WHERE uri = ?)",
                    "AND remote_addr = ?",
                    "AND parent IS NULL;",
                ],
                (uri, comment["remote_addr"]),
            ).fetchall()

            if len(rv) >= self.conf.getint("direct-reply"):
                return False, "direct-reply", "%i direct responses to %s" % (len(rv), uri)

        # block replies to self unless :param:`reply-to-self` is enabled
        elif self.conf.getboolean("reply-to-self") is False:
            rv = self.db.execute(
                ["SELECT id FROM comments WHERE    remote_addr = ?", "AND id = ?", "AND ? - created < ?"],
                (comment["remote_addr"], comment["parent"], time.time(), self.max_age),
            ).fetchall()

            if len(rv) > 0:
                # Allow the reply anyway if someone else was the last to reply to
                # that comment: this is a genuine back-and-forth (A comments,
                # B replies to A, A replies to B), not the commenter padding
                # their own still-editable comment. Gating on the most recent
                # published reply (rather than "any foreign reply ever") means
                # each foreign reply only unlocks a single self-reply, so the
                # commenter cannot keep padding once they have answered.
                last = self.db.execute(
                    [
                        "SELECT remote_addr FROM comments",
                        "WHERE parent = ? AND mode = 1",
                        "ORDER BY created DESC LIMIT 1;",
                    ],
                    (comment["parent"],),
                ).fetchone()

                if last is None or last[0] == comment["remote_addr"]:
                    return False, "reply-to-self", "edit time frame is still open"

        # require email if :param:`require-email` is enabled
        if self.conf.getboolean("require-email") and not comment.get("email"):
            return False, "require-email", "email address required but not provided"

        # require author if :param:`require-author` is enabled
        if self.conf.getboolean("require-author") and not comment.get("author"):
            return False, "require-author", "author address required but not provided"

        return True, "", ""

    def _spam(self, uri, comment):
        return True, "", ""
