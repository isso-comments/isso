# -*- encoding: utf-8 -*-

import tempfile
from os.path import join, dirname

from isso.core import Config

from isso.db import Adapter
from isso.migrate import disqus


def test_disqus():

    xml = join(dirname(__file__), "disqus.xml")

    db = Adapter("sqlite:///:memory:", Config.load(None))
    disqus(db, xml)

    assert db.threads["/"]["title"] == "Hello, World!"
    assert db.threads["/"]["id"] == 1


    a = db.comments.get(1)

    assert a["author"] == "peter"
    assert a["email"] == "foo@bar.com"

    b = db.comments.get(2)
    assert b["parent"] == a["id"]
