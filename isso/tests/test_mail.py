# -*- encoding: utf-8 -*-

# Test mail format customization

from __future__ import unicode_literals

import unittest
import os
import json
import tempfile

try:
    from urllib.parse import quote
except ImportError:
    from urllib import quote

from werkzeug.wrappers import Response
from isso import Isso, core, config, local, dist
from isso.utils import http
from fixtures import curl, loads, FakeIP, JSONClient
http.curl = curl

from isso.ext.notifications import SMTP


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
        self.public_endpoint = conf.get("server", "public-endpoint") or local("host")

        self.smtp = SMTP(self.app)

    def tearDown(self):
        os.unlink(self.path)

    def testAnonymous_plain(self):
        """Test if anonymous works (plain part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                             author="Anonymous",
                             comment=rv["text"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAnonymous_html(self):
        """Test if anonymous works (html part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous  \n__I love you.__", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author="Anonymous",
                             comment="<p>From Anonymous<br>\n<strong>I love you.</strong></p>",
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAnonymousRuntimeError_plain(self):
        """Test what will happen when these happens (plain part):
        1. The language is set to the one which will cause translate function to throw RuntimeError
        2. The default template could not be found.
        """
        self.conf.set("mail", "language", "tk")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                             author="Anonymous",
                             comment=rv["text"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAnonymousRuntimeError_html(self):
        """Test what will happen when these happens (html part):
        1. The language is set to the one which will cause translate function to throw RuntimeError
        2. The default template could not be found.
        """
        self.conf.set("mail", "language", "tk")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From __Anonymous__", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author="Anonymous",
                             comment="<p>From <strong>Anonymous</strong></p>",
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAnonymousStringNotAvailable_plain(self):
        """Test what will happen when these happens (plain part):
        1. The language is set to the one which will cause translate function to return an undesired string
        2. The default template could not be found.
        """
        self.conf.set("mail", "language", "aa")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Anonymous", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                             author="Anonymous",
                             comment=rv["text"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAnonymousStringNotAvailable_html(self):
        """Test what will happen when these happens (html part):
        1. The language is set to the one which will cause translate function to return an undesired string
        2. The default template could not be found.
        """
        self.conf.set("mail", "language", "aa")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From **Anonymous**", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author="Anonymous",
                             comment="<p>From <strong>Anonymous</strong></p>",
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testEmail_plain(self):
        """Test the mail when the author has an email (plain part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From Email user", "author": "Sim", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = "sim@snorl.ax"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             email=rv["email"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testEmail_html(self):
        """Test the mail when the author has an email (html part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps({"text": "From _Email_ user", "author": "Sim", "website": "", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = "sim@snorl.ax"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} &lt;<a href="mailto:{email}">{email}</a>&gt; wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment="<p>From <em>Email</em> user</p>",
                             email=rv["email"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testLanguage_plain(self):
        """Test (plain part):
        1. The mail template when the lang is set to a language whose template is available
        2. The "Anonymous" is translated correctly.
        """
        self.conf.set("mail", "language", "de")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "This is de.", "website": "https://snorl.ax", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} hat geschrieben:\n\n{comment}\n\nURL des Benutzers: {website}\nIP Adresse: {ip}\nLink zum Kommentar: {com_link}\n\n---\nKommentar löschen: {del_link}\n\n\n".format(
                             author="Anonym",
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testLanguage_html(self):
        """Test (html part):
        1. The mail template when the lang is set to a language whose template is available
        2. The "Anonymous" is translated correctly.
        """
        self.conf.set("mail", "language", "de")
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "This is __de__.", "website": "https://snorl.ax", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} hat geschrieben:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tURL des Benutzers: <a href="{website}">{website}</a>\n\t<br>\n\t\n\tIP Adresse: {ip}\n\t<br>\n\t\n\n\tLink zum Kommentar: <a href="{com_link}">Hier klicken</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tKommentar löschen: <a href="{del_link}">Hier klicken</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author="Anonym",
                             comment="<p>This is <strong>de</strong>.</p>",
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAdminClass_plain(self):
        """Test the approval mail of first-class comment waiting for approval (plain part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a first-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        rv["mode"] = 2
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True),
                         "{author} wrote:\n\n{comment}\n\nUser's URL: {website}\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\nActivate comment: {act_link}\n\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             act_link=self.public_endpoint + "/id/%i/activate/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testAdminClass_html(self):
        """Test the approval mail of first-class comment waiting for approval (html part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "_This_ is a **first-class** comment",
                 "author": "Sim",
                 "website": "https://snorl.ax", }))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        rv = loads(rv.data)
        rv["email"] = ""
        rv["remote_addr"] = "127.0.0.1"
        rv["mode"] = 2
        self.assertEqual(self.smtp.format(thread_test, rv, None, admin=True, part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tUser\'s URL: <a href="{website}">{website}</a>\n\t<br>\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\tActivate comment: <a href="{act_link}">Click Here</a>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment="<p><em>This</em> is a <strong>first-class</strong> comment</p>",
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             del_link=self.public_endpoint + "/id/%i/delete/" % rv["id"] + self.smtp.key,
                             act_link=self.public_endpoint + "/id/%i/activate/" % rv["id"] + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testUserClass_plain(self):
        """Test reply notification (plain part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"]),
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testUserClass_html(self):
        """Test reply notification (html part)"""
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "__THis__ is a _sub-class_ comment  \n[Hello](https://snorl.ax)",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"], part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tUnsubcribe from this conversation: <a href="{unsubscribe}">Click Here</a>\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment='<p><strong>THis</strong> is a <em>sub-class</em> comment<br>\n<a href="https://snorl.ax" rel="nofollow noopener">Hello</a></p>',
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateDir_plain(self):
        """When the template is set to an available directory (plain part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True),
            "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                author="Anonymous",
                email=pa["email"],
                comment=pa["text"],
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"]),
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateDir_html(self):
        """When the template is set to an available directory (html part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '__...__'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "__THis__ is a _sub-class_ comment  \n[Hello](https://snorl.ax)",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True, part="html"),
            '<html>\n<p>{author} &lt;<a href="mailto:{email}">{email}</a>&gt; wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\n\t\n\tIP address: {ip}\n\t<br>\n\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\n\n\n</p>\n</html>\n'.format(
                author="Anonymous",
                email=pa["email"],
                comment="<p><strong>...</strong></p>",
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"], part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\n\tUnsubcribe from this conversation: <a href="{unsubscribe}">Click Here</a>\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment='<p><strong>THis</strong> is a <em>sub-class</em> comment<br>\n<a href="https://snorl.ax" rel="nofollow noopener">Hello</a></p>',
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateSingle_plain(self):
        """When the template is set to an available file (plain part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir", "comment.plain"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True),
            "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                author="Anonymous",
                email=pa["email"],
                comment=pa["text"],
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"]),
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateSingle_html(self):
        """When the template is set to an available file (html part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "test_mail_dir", "comment.html"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...__you__'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "__THis__ is a _sub-class_ comment  \n[Hello](https://snorl.ax)",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True, part="html"),
            '<html>\n<p>{author} &lt;<a href="mailto:{email}">{email}</a>&gt; wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                author="Anonymous",
                email=pa["email"],
                comment="<p>...<strong>you</strong></p>",
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"], part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tUnsubcribe from this conversation: <a href="{unsubscribe}">Click Here</a>\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment='<p><strong>THis</strong> is a <em>sub-class</em> comment<br>\n<a href="https://snorl.ax" rel="nofollow noopener">Hello</a></p>',
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateUnvailable_plain(self):
        """When the template is set to an unavailable path (plain part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "unavailable_path"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '...'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "THis is a sub-class comment",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True),
            "{author} <{email}> wrote:\n\n{comment}\n\nIP address: {ip}\nLink to comment: {com_link}\n\n---\nDelete comment: {del_link}\n\n\n".format(
                author="Anonymous",
                email=pa["email"],
                comment=pa["text"],
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"]),
                         "{author} wrote:\n\n{comment}\n\nLink to comment: {com_link}\n\n---\nUnsubcribe from this conversation: {unsubscribe}\n\n".format(
                             author=rv["author"],
                             comment=rv["text"],
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))

    def testCustomTemplateUnvailable_html(self):
        """When the template is set to an unavailable path (html part)"""
        self.conf.set("mail", "template", os.path.join(dist.location, "isso", "tests", "unavailable_path"))
        self.smtp = SMTP(self.app)
        thread_test = {"uri": "/aaa", "title": "Hello isso!"}
        pa = self.post('/new?uri=test', data=json.dumps({'text': '__...__'}))
        rv = self.post(
            '/new?uri=%2Fpath%2F',
            data=json.dumps(
                {"text": "__THis__ is a *sub-class* comment  \n[Hello](https://snorl.ax)",
                 "author": "Sim",
                 "website": "https://snorl.ax",
                 "parent": 1}))
        self.assertEqual(rv.status_code, 201)
        self.assertIn("Set-Cookie", rv.headers)
        pa = loads(pa.data)
        pa["email"] = "sim@snorl.ax"
        pa["remote_addr"] = "127.0.0.1"
        self.assertEqual(
            self.smtp.format(thread_test, pa, None, admin=True, part="html"),
            '<html>\n<p>{author} &lt;<a href="mailto:{email}">{email}</a>&gt; wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\t\n\tIP address: {ip}\n\t<br>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tDelete comment: <a href="{del_link}">Click Here</a>\n\t<br>\n\t\n\t\n\t\n\n</p>\n</html>\n'.format(
                author="Anonymous",
                email=pa["email"],
                comment='<p><strong>...</strong></p>',
                website=pa["website"],
                ip=pa["remote_addr"],
                del_link=self.public_endpoint + "/id/%i/delete/" % pa["id"] + self.smtp.key,
                com_link=local("origin") + thread_test["uri"] + "#isso-%i" % pa["id"]))

        rv = loads(rv.data)
        rv["email"] = "hello@example.com"
        rv["remote_addr"] = "127.0.0.1"
        self.assertEqual(self.smtp.format(thread_test, rv, pa, recipient=pa["email"], part="html"),
                         '<html>\n<p>{author} wrote:</p>\n\n<p>{comment}</p>\n\n<p>\n\t\n\n\tLink to comment: <a href="{com_link}">Click Here</a>\n</p>\n\n<hr>\n\n<p>\n\n\t\n\tUnsubcribe from this conversation: <a href="{unsubscribe}">Click Here</a>\n\t\n\n</p>\n</html>\n'.format(
                             author=rv["author"],
                             comment='<p><strong>THis</strong> is a <em>sub-class</em> comment<br>\n<a href="https://snorl.ax" rel="nofollow noopener">Hello</a></p>',
                             website=rv["website"],
                             ip=rv["remote_addr"],
                             unsubscribe=self.public_endpoint + "/id/%i/unsubscribe/" % pa["id"] + quote(pa["email"]) + "/" + self.smtp.key,
                             com_link=local("origin") + thread_test["uri"] + "#isso-%i" % rv["id"]))
