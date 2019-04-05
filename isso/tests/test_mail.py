# -*- encoding: utf-8 -*-

# Test mail format customization

import unittest
import os
import tempfile

from isso import Isso, core, config, dist

from fixtures import curl, loads, FakeIP, JSONClient
 
class TestMail(unittest.TestCase):
    
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(os.path.join(dist.location, "share", "isso.conf"))
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")
        self.conf = conf
        
        class App(Isso, core.Mixin):
            pass

        self.app = App(conf)
        self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")

        self.client = JSONClient(self.app, Response)
        self.get = self.client.get
        self.put = self.client.put
        self.post = self.client.post
        self.delete = self.client.delete
         
    def testTemplate(self):
        langs = ["de", "fr", "ja", "zh", "zh_TW", "zh_CN"]
        self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment.plain")))
        self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment.html")))
        for lang in langs:
            self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment_%s.plain"%lang)))
            self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment_%s.html"%lang)))
    
    def testTitle(self):
        self.assertEqual(self.conf.get("mail", "title_admin").format(title="test"), "test")
        self.assertEqual(self.conf.get("mail", "title_user").format(title="test"), "Re: New comment posted on test")