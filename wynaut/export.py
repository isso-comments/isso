# -*- encoding: utf-8 -*-

from __future__ import unicode_literals

import sys

from io import StringIO
from csv import writer as csv_writer

from isso.db import SQLite3
from isso.core import Config
from isso.compat import PY2K, text_type as str

from wynaut import get_parser

if PY2K:
    _StringIO = StringIO
    class StringIO(_StringIO):

        def write(self, data):
            data = data.decode("utf-8")
            return super(StringIO, self).write(data)


def csv(db, threads=True, comments=False):
    """
    Print threads *or* comments formatted as CSV (Excel dialect).  Rows are
    separated by comma and `None` is replaced with the empty string.

    The first line is always a row containing the identifiers per column.
    """

    fp = StringIO()
    writer = csv_writer(fp, dialect="excel")

    fmt = lambda val: "" if val is None else val

    if threads:
        writer.writerow(["id", "uri", "title"])
        query = db.execute("SELECT id, uri, title FROM threads").fetchall()
    else:
        fields = ["id", "parent", "created", "modified", "mode", "remote_addr",
                  "author", "email", "website", "likes", "dislikes", "text"]
        writer.writerow(fields)
        query = db.execute("SELECT %s FROM comments" % ",".join(fields))

    for row in query:
        writer.writerow(map(lambda s: str(fmt(s)).encode("utf-8"), row))

    fp.seek(0)
    for line in fp:
        sys.stdout.write(line.encode("utf-8"))


def main():

    parser = get_parser("export to various formats")
    parser.add_argument("-t", "--to", dest="type", choices=["csv"],
        help="export format")

    group = parser.add_mutually_exclusive_group()
    group.add_argument("--threads", action="store_true",
        help="export threads (only for csv)")
    group.add_argument("--comments", action="store_true",
        help="export comments (only for csv)")

    args = parser.parse_args()

    conf = Config.load(args.conf)
    db = SQLite3(conf.get("general", "dbpath"), conf)

    if args.type == "csv":

        if not any((args.threads, args.comments)):
            raise SystemExit("CSV export needs either --comments or --threads")

        csv(db, args.threads, args.comments)
