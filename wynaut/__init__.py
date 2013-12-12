# -*- encoding: utf-8 -*-

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import os
import tempfile

from argparse import ArgumentParser

from isso.db import SQLite3
from isso.core import Config

from wynaut.imprt import Disqus

try:
    input = raw_input
except NameError:
    pass


def main():

    parser = ArgumentParser(description="manage Isso")
    subparser = parser.add_subparsers(help="commands", dest="command")

    parser.add_argument('--version', action='version', version='%(prog)s' + dist.version)
    parser.add_argument('-c', dest="conf", default=os.environ.get("ISSO_SETTINGS"),
                        metavar="/etc/isso.conf", help="set configuration file")

    imprt = subparser.add_parser('import', help="import Disqus XML export")
    imprt.add_argument("dump", metavar="FILE")
    imprt.add_argument("-f", "--force", dest="force", action="store_true",
                       help="force actions")
    imprt.add_argument("-n", "--dry-run", dest="dryrun", action="store_true",
                       help="perform a trial run with no changes made")

    args = parser.parse_args()
    conf = Config.load(args.conf)

    if args.command == "import":
        xxx = tempfile.NamedTemporaryFile()
        dbpath = conf.get("general", "dbpath") if not args.dryrun else xxx.name

        dsq = Disqus(args.dump)
        db = SQLite3(dbpath, conf)

        if db.execute("SELECT * FROM comments").fetchone():
            if not args.force and input("Isso DB is not empty! Continue? [y/N]: ") not in ("y", "Y"):
                raise SystemExit("Abort.")

        dsq.migrate(db)
