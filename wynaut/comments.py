# -*- encoding: utf-8 -*-

from __future__ import unicode_literals, print_function

import sys
import os
import io
import shlex
import tempfile
import subprocess

from isso.db import SQLite3
from isso.core import Config

from wynaut import get_parser


def read(fp):

    comment = {}

    for line in fp:

        if line == "---\n":
            break

        key, value = line.split(":", 1)
        comment[key.strip()] = value.strip()

    comment["text"] = fp.read()

    for key in ("created", "modified"):
        if comment.get(key):
            comment[key] = float(comment[key])

    for key in ("likes", "dislikes"):
        if comment.get(key):
            comment[key] = int(comment[key])

    return comment


def write(fp, comment, empty=False):

    for key in ("author", "email", "website", "remote_addr", "created",
                "modified", "likes", "dislikes"):
        if comment.get(key) or empty:
            fp.write("{0}: {1}\n".format(key, comment[key] or ""))

    fp.write("---\n")
    fp.write(comment["text"])


def main():
    parser = get_parser("Administrate comments stored in Isso's SQLite3.")
    subparsers = parser.add_subparsers(help="commands", dest="command")

    parser_list = subparsers.add_parser("list", help="list comments")

    parser_show = subparsers.add_parser("show", help="show comment")
    parser_show.add_argument("id", metavar="N", type=int)
    parser_show.add_argument("--empty", dest="empty", action="store_true")

    parser_edit = subparsers.add_parser("edit", help="edit comment")
    parser_edit.add_argument("id", metavar="N", type=int)
    parser_edit.add_argument("--empty", dest="empty", action="store_true")

    parser_rm = subparsers.add_parser("rm", help="remove comment")
    parser_rm.add_argument("id", metavar="N", type=int)
    parser_edit.add_argument("-r", dest="recursive", action="store_true")

    args = parser.parse_args()

    conf = Config.load(args.conf)
    db = SQLite3(conf.get("general", "dbpath"), conf)

    if args.command == "show":
        if db.comments.get(args.id) is None:
            raise SystemExit("no such id: %i" % args.id)
        write(sys.stdout, db.comments.get(args.id), empty=args.empty)

    if args.command == "list":
        for (id, text) in db.execute("SELECT id, text FROM comments").fetchall():
            sys.stdout.write("{0:>3}: {1}\n".format(id, text.replace("\n", " ")).encode("utf-8"))
            sys.stdout.flush()

    if args.command == "edit":
        if db.comments.get(args.id) is None:
            raise SystemExit("no such id: %i" % args.id)

        xxx = tempfile.NamedTemporaryFile()

        with io.open(xxx.name, "w") as fp:
            write(fp, db.comments.get(args.id), empty=args.empty)

        retcode = subprocess.call(shlex.split(
            os.environ.get("EDITOR", "nano")) + [xxx.name])

        if retcode < 0:
            raise SystemExit("Child was terminated by signal %i" % -retcode)

        with io.open(xxx.name, "r") as fp:
            db.comments.update(args.id, read(fp))

    if args.command == "rm":

        if not args.recursive:
            rv = db.comments.delete(args.id)

            if rv:
                print("comment is still referenced")

