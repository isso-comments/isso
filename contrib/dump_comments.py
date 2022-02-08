#!/usr/bin/env python
# -*- encoding: utf-8 -*-
#
# The MIT License (MIT)
#
# Copyright (c) 2020 Lucas Cimon.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Dump isso comments as text

The script can be run like this:

    contrib/dump_comments.py .../path/to/isso.db --sort-by-last-reply

To get a list of all available options:

    contrib/dump_comments.py --help

By installing the optional colorama dependency, you'll get a colored output.
An example of output can be found at https://github.com/posativ/isso/issues/634
"""

import argparse
import sqlite3
from collections import defaultdict, namedtuple
from datetime import date
from textwrap import indent


class ColorFallback():
    __getattr__ = lambda self, name: ''  # noqa: E731


try:
    from colorama import Fore, Style, init
    init()  # needed for Windows
except ImportError:  # fallback so that the imported classes always exist
    Fore = Style = ColorFallback()


Comment = namedtuple('Comment', ('uri', 'id', 'parent', 'created', 'text', 'author', 'email', 'website', 'likes', 'dislikes', 'replies'))

INDENT = '    '
QUERY = 'SELECT uri, comments.id, parent, created, text, author, email, website, likes, dislikes FROM comments INNER JOIN threads on comments.tid = threads.id'


def main():
    args = parse_args()
    if not args.colors:
        global Fore, Style
        Fore = Style = ColorFallback()
    db = sqlite3.connect(args.db_path)
    comments_per_uri = defaultdict(list)
    for result in db.execute(QUERY).fetchall():
        comment = Comment(*result, replies=[])
        comments_per_uri[comment.uri].append(comment)
    root_comments_per_sort_date = {}
    for comments in comments_per_uri.values():
        comments_per_id = {comment.id: comment for comment in comments}
        root_comments, sort_date = [], None
        for comment in comments:
            if comment.parent:  # == this is a "reply" comment
                comments_per_id[comment.parent].replies.append(comment)
                if args.sort_by_last_reply and (sort_date is None or comment.created > sort_date):
                    sort_date = comment.created
            else:
                root_comments.append(comment)
                if sort_date is None or comment.created > sort_date:
                    sort_date = comment.created
        root_comments_per_sort_date[sort_date] = root_comments
    for _, root_comments in sorted(root_comments_per_sort_date.items(), key=lambda pair: pair[0]):
        print(Fore.MAGENTA + args.url_prefix + root_comments[0].uri + Fore.RESET)
        for comment in root_comments:
            print_comment(INDENT, comment)
            for comment in comment.replies:
                print_comment(INDENT * 2, comment)
        print()


def print_comment(prefix, comment):
    author = comment.author or 'Anonymous'
    email = comment.email or ''
    website = comment.website or ''
    when = date.fromtimestamp(comment.created)
    popularity = ''
    if comment.likes:
        popularity = '+{.likes}'.format(comment)
    if comment.dislikes:
        if popularity:
            popularity += '/'
        popularity = '-{.dislikes}'.format(comment)
    print(prefix + '{Style.BRIGHT}{author}{Style.RESET_ALL} {Style.DIM}- {email} {website}{Style.RESET_ALL} {when} {Style.DIM}{popularity}{Style.RESET_ALL}'.format(Style=Style, **locals()))
    print(indent(comment.text, prefix))


def parse_args():
    parser = argparse.ArgumentParser(description='Dump all Isso comments in chronological order, grouped by replies',
                                     formatter_class=ArgparseHelpFormatter)
    parser.add_argument('db_path', help='File path to Isso Sqlite DB')
    parser.add_argument('--sort-by-last-reply', action='store_true', help='By default comments are sorted by "parent" comment date, this sort comments based on the last replies')
    parser.add_argument('--url-prefix', default='', help='Optional domain name to prefix to pages URLs')
    parser.add_argument('--no-colors', action='store_false', dest='colors', default=True, help='Disabled colored output')
    return parser.parse_args()


class ArgparseHelpFormatter(argparse.RawTextHelpFormatter, argparse.ArgumentDefaultsHelpFormatter):
    pass


if __name__ == '__main__':
    main()
