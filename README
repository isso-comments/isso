Isso – Ich schrei sonst
=======================

You love static blog generators (especially [Acrylamid][1] *cough*) and the
only option to interact with the community is [Disqus][2]. There's nothing
wrong with it, but if you care about the privacy of your audience you are
better off with a comment system that is under your control. This is, were
Isso comes into play.

[1]: https://github.com/posativ/acrylamid
[2]: http://disqus.com/


Features
--------

* [CRUD][https://en.wikipedia.org/wiki/Create,_read,_update_and_delete] comments
* SQLite
* quite nice, but unfinished client-side JS


Roadmap
-------

- Ping/TrackBack™ support
- simple admin interface
- spam filtering using [http:bl][3]

[3]: https://www.projecthoneypot.org/


Installation
------------

Probably `git clone https://github.com/posativ/isso.git`, `python setup.py develop`
inside a virtualenv. Then start `isso` with

    ~> isso run

You can now leave a comment at <http://localhost:8080/static/post.html> hopefully.
The admin interface password is `p@$$w0rd`, you may change this with a custom cfg
file that I'll document later. You find the admin interface at <http://localhost:8080/admin/>.


Migration from Disqus
---------------------

Go to [Disqus.com](https://disqus.com/) and export your "forum" as XML.

    ~> isso import /path/to/ur/dump.xml

That's it. <del>Visit your admin page to see all threads.</del> If it doesn't work for
you, please file in a bug report \*including\* your dump.


API (a draft)
-------------

To fetch all comments for `http://example.tld/foo-bar/`, run

::

    $ curl http://example.tld/isso?uri=%2Ffoo-bar%2F

To write a comment, you have to POST a JSON dictionary with the following
key-value pairs. Text is mandatory otherwise you'll get a 400 Bad Request.
You'll also get a 400 when your JSON is invalid.

Let's say you want to comment on /foo-bar/

    $ curl http://example.tld/isso/new?uri=%2Ffoo-bar%2F -X POST -d \
        '{
            "text": "Lorem ipsum ...",
            "name": "Hans", "email": "foo@bla.org", "website": "http://blog/log/"
         }'

This will set a cookie, that expires in a few minutes (15 minutes per default).
This cookie allows you do modify or delete your comment. Don't try to modify
that cookie, it is cryptographically signed. If your cookie is outdated or
modified, you'll get a 403 Forbidden.

For each comment you'll post, you get an unique cookie. Let's try to remove
your comment::

    $ curl -X DELETE 'http://example.tld/isso?uri=%2Ffoo-bar%2F&id=1'

If your comment has been referenced by another comment, your comment will be
cleared but not deleted to retain depending comments.

Alternatives
------------

- `talkatv <https://github.com/talkatv/talkatv>`_ – Python
- `Juvia <https://github.com/phusion/juvia)>`_ – Ruby on Rails
- `Tildehash.com <http://www.tildehash.com/?article=why-im-reinventing-disqus>`_ – PHP
- `SO: Unobtrusive, self-hosted comments <http://stackoverflow.com/q/2053217>`_
