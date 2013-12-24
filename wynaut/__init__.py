# -*- encoding: utf-8 -*-

import pkg_resources
dist = pkg_resources.get_distribution("isso")

import os
from argparse import ArgumentParser, SUPPRESS



def get_parser(desc):

    parser = ArgumentParser(description=desc)

    parser.add_argument('--version', action='version', version='%(prog)s' + dist.version,
                        help=SUPPRESS)
    parser.add_argument('-c', dest="conf", default=os.environ.get("ISSO_SETTINGS"),
                        metavar="/etc/isso.conf", help="set configuration file")

    return parser
