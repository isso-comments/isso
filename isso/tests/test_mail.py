# -*- encoding: utf-8 -*-

# Test mail format customization

import unittest
import os

from isso import Isso, core, config, dist
 
class TestMail(unittest.TestCase):
      
    def setUp(self):
        conf = config.load(os.path.join(dist.location, "share", "isso.conf"))
        self.conf = conf
  
#         class App(Isso, core.Mixin):
#             pass
#   
#         self.app = App(conf)
#         self.app.wsgi_app = FakeIP(self.app.wsgi_app, "192.168.1.1")
#   
#         self.client = JSONClient(self.app, Response)
#         self.get = self.client.get
#         self.put = self.client.put
#         self.post = self.client.post
#         self.delete = self.client.delete

    def testAnonymous(self):
        ano_cases = {
            "bg": "анонимен",
            "cs": "Anonym",
            "da": "Anonym",
            "de": "Anonym",
            "el_GR": "Ανώνυμος",
            "en": "Anonymous",
            "eo": "Sennoma",
            "es": "Anónimo",
            "fa": "ناشناس",
            "fi": "Nimetön",
            "fr": "Anonyme",
            "hr": "Anonimno",
            "hu": "Névtelen",
            "it": "Anonimo",
            "nl": "Anoniem",
            "pl": "Anonim",
            "ru": "Аноним",
            "sv": "Anonym",
            "vi": "Nặc danh",
            "zh": "匿名",
            "zh_CN": "匿名",
            "zh_TW": "匿名",
            "ja": "アノニマス"
        }
        for key, value in ano_cases.items():
            self.assertEqual(self.conf.get("mail", "anonymous_%s"%key), value)
         
    def testTemplate(self):
        langs = ["de", "fr", "ja", "zh", "zh_TW", "zh_CN"]
        self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment.plain")), True)
        self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment.html")), True)
        for lang in langs:
            self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment_%s.plain"%lang)), True)
            self.assertTrue(os.path.isfile(os.path.join(dist.location, "isso", "templates", "comment_%s.html"%lang)), True)
    
    def testTitle(self):
        self.assertTrue(self.conf.get("mail", "title_admin").format(title="test"), "test")
        self.assertTrue(self.conf.get("mail", "title_user").format(title="test"), "Re: New comment posted on test")