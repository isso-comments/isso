# -*- encoding: utf-8 -*-

import tempfile
from os.path import join, dirname

from isso.core import Config

from isso.db import SQLite3
from isso.migrate import disqus


def test_disqus():

    xml = join(dirname(__file__), "disqus.xml")
    xxx = tempfile.NamedTemporaryFile()

    db = SQLite3(xxx.name, Config.load(None))
    disqus(db, xml)

    assert db.threads["/"]["title"] == "Hello, World!"
    assert db.threads["/"]["id"] == 1


    a = db.comments.get(1)

    assert a["author"] == "peter"
    assert a["email"] == "foo@bar.com"

    b = db.comments.get(2)
    assert b["parent"] == a["id"]
