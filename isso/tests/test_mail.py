# -*- encoding: utf-8 -*-

# Test mail format customization

from __future__ import unicode_literals

import unittest
import os
import re
import json
import tempfile

try:
    from urllib.parse import urlencode
except ImportError:
    from urllib import urlencode
    
try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from werkzeug.wrappers import Response

from getpass import getpass

from isso import Isso, core, config, local, dist
from isso.utils import http
from isso.views import comments

from isso.compat import iteritems

from fixtures import curl, loads, FakeIP, JSONClient
http.curl = curl

from isso.ext.notifications import SMTP

smtp_host = input("Enter the SMTP host (Leave it blank to use localhost): ")
smtp_port = input("Enter the SMTP port (Leave it blank to use 587): ")
smtp_security = input("Enter the SMTP security option (Available options: none, starttls or ssl. Default: starttls)")
smtp_username = input("Enter the username (Leave it blank if you don't need it in the test): ")
if smtp_username:
    smtp_password = getpass("Enter the password (Leave it blank if you don't need it in the test): ")

class TestMail(unittest.TestCase):
    
    def setUp(self):
        fd, self.path = tempfile.mkstemp()
        conf = config.load(os.path.join(dist.location, "share", "isso.conf"))
        conf.set("general", "dbpath", self.path)
        conf.set("guard", "enabled", "off")
        conf.set("hash", "algorithm", "none")

        if smtp_host:
            self.conf.set("smtp", "host", smtp_host)
        if smtp_port:
            self.conf.set("smtp", "port", smtp_port)
        if smtp_security:
            self.conf.set("smtp", "security", smtp_security)
        if smtp_username:
            self.conf.set("smtp", "username", smtp_username)
            if smtp_password:
                self.conf.set("smtp", "password", smtp_password)

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
        self.public_endpoint = conf.get("server", "public-endpoint") or local("host")
        self.smtp = SMTP(self.app)
         
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
        
    def testAnonymous(self):
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "From Anonymous", "website": "",}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin = True), 
                         "{author} wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(author = "Anonymous",
                                                                                                                                                          comment = rv["text"],
                                                                                                                                                          ip = rv["remote_addr"],
                                                                                                                                                          del_link = self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.isso.sign(rv["id"]),
                                                                                                                                                          com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))
        
        
    def testEmail(self):
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "From Email user", "author": "Sim", "website": "",}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = "sim@snorl.ax"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin = True), 
                         "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(author = rv["author"],
                                                                                                                                                                   comment = rv["text"],
                                                                                                                                                                   email = rv["email"],
                                                                                                                                                                   ip = rv["remote_addr"],
                                                                                                                                                                   del_link = self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.isso.sign(rv["id"]),
                                                                                                                                                                   com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testLanguage(self):
        self.conf.set("mail", "language", "de")
        self.smtp = SMTP(self.app)
        
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "This is de.", 
                   "author": "Sim",
                   "website": "https://snorl.ax",}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin = True), 
                         "{author} hat geschrieben:\n\n{comment}\n\nURL des Benutzers: {website}\nIP Adresse: {ip}\nLink zum Kommentar: {com_link}\n\n---\nKommentar löschen: {del_link}\n\n\n".format(author = rv["author"],
                                                                                                                                                                              comment = rv["text"],
                                                                                                                                                                              website = rv["website"],
                                                                                                                                                                              ip = rv["remote_addr"],
                                                                                                                                                                              del_link = self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.isso.sign(rv["id"]),
                                                                                                                                                                              com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))
        
#         case 1: test the approval mail offirst-class comment waiting for approval

    def testAdminClass(self):
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "THis is a first-class comment", 
                   "author": "Sim",
                   "website": "https://snorl.ax",}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        rv["mode"] = 2
        key = self.smtp.isso.sign(rv["id"])
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin = True), 
                         "{author} wrote:\n\n{comment}\n\nUser's URL: {website}\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\nActivate comment: {act_link}\n\n\n".format(author = rv["author"],
                                                                                                                                                                              comment = rv["text"],
                                                                                                                                                                              website = rv["website"],
                                                                                                                                                                              ip = rv["remote_addr"],
                                                                                                                                                                              del_link = self.public_endpoint + "/id/%i/delete/" % rv["id"] + key,
                                                                                                                                                                              act_link = self.public_endpoint + "/id/%i/activate/" % rv["id"] + key,
                                                                                                                                                                              com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))
#         case 2: test reply notification 

    def testUserClass(self):
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "THis is a sub-class comment", 
                   "author": "Sim",
                   "website": "https://snorl.ax",
                   "parent": 1}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient = pa["email"]), 
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(author = rv["author"],
                                                                                                                                                              comment = rv["text"],
                                                                                                                                                              website = rv["website"],
                                                                                                                                                              ip = rv["remote_addr"],
                                                                                                                                                              unsubscribe = self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.isso.sign(('unsubscribe', pa["email"])),
                                                                                                                                                              com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))
        
    def testCustomTemplateDir(self):
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "THis is a sub-class comment", 
                   "author": "Sim",
                   "website": "https://snorl.ax",
                   "parent": 1}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, pa, None, admin = True), 
                 "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(author = "Anonymous",
                                                                                                                                                          email = pa["email"],
                                                                                                                                                          comment = pa["text"],
                                                                                                                                                          website = pa["website"],
                                                                                                                                                          ip = pa["remote_addr"],
                                                                                                                                                          del_link = self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.isso.sign(pa["id"]),
                                                                                                                                                          com_link = local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient = pa["email"]), 
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(author = rv["author"],
                                                                                                                                                              comment = rv["text"],
                                                                                                                                                              website = rv["website"],
                                                                                                                                                              ip = rv["remote_addr"],
                                                                                                                                                              unsubscribe = self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.isso.sign(('unsubscribe', pa["email"])),
                                                                                                                                                              com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))


    def testCustomTemplateSingle(self):
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir", "comment.plain"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post('/new?uri=%2Fpath%2F',
               data=json.dumps({"text": "THis is a sub-class comment", 
                   "author": "Sim",
                   "website": "https://snorl.ax",
                   "parent": 1}))  
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, pa, None, admin = True), 
                 "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(author = "Anonymous",
                                                                                                                                                          email = pa["email"],
                                                                                                                                                          comment = pa["text"],
                                                                                                                                                          website = pa["website"],
                                                                                                                                                          ip = pa["remote_addr"],
                                                                                                                                                          del_link = self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.isso.sign(pa["id"]),
                                                                                                                                                          com_link = local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient = pa["email"]), 
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(author = rv["author"],
                                                                                                                                                              comment = rv["text"],
                                                                                                                                                              website = rv["website"],
                                                                                                                                                              ip = rv["remote_addr"],
                                                                                                                                                              unsubscribe = self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.isso.sign(('unsubscribe', pa["email"])),
                                                                                                                                                              com_link = local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))


