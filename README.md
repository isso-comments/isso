Isso – Ich schrei sonst
=======================

You love static blog generators (especially [Acrylamid][1] *cough*) and the
only option to interact with the community is [Disqus][2]. There's nothing
wrong with it, but if you care about the privacy of your audience you are
better off with a comment system that is under your control. This is, where
Isso comes into play.

[1]: https://github.com/posativ/acrylamid
[2]: https://disqus.com/

**[Screenshot @2013-09-13](http://posativ.org/~tmp/isso-preview.png)** |
**[Screenshot @2013-10-03](http://rw.posativ.org/n1v/o)** |
**[Try Yourself!](http://posativ.org/isso/static/post.html)** (in case it's not crashed ;-)

Isso is not stable (pretty far from that state) and the database format may
change without any backwards compatibility. Just saying.


Features
--------

* [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) comments
* SQLite backend, Disqus import
* client-side JS (currently 61kb minified, 21kb gzipped)
* I18N, available in german and english (also fallback)


Roadmap
-------

- Ping/TrackBack™ support
- simple admin interface (needs contributor)
- spam filtering


Installation
------------

Note, there is currently no PyPi release, but I'll upload a snapshot
infrequently. Nevertheless, here are the requirements:

- Python 2.6, 2.7 or 3.3
- easy_install or pip

Install Isso (and its dependencies) with:

    ~> pip install isso

Before you start, you may want to import comments from
[Disqus.com](https://disqus.com/):

    ~> isso import ~/Downloads/user-2013-09-02T11_39_22.971478-all.xml
    [100%]  53 threads, 192 comments

You start the server via (try to visit [http://localhost:8080/static/post.html]()).

    ~> isso run

If that is working, you may want to [edit the configuration](https://github.com/posativ/isso/blob/master/docs/CONFIGURATION.rst).


Webserver Configuration
-----------------------

This part is not fun, I know. I have prepared two possible setups for nginx,
using Isso on the same domain as the blog, and on a different domain. Each
setup has its own benefits.

### Isso on a Sub URI

Let's assume you want Isso on `/isso`, use the following nginx snippet:

```nginx
server {
    listen       [::]:80;
    listen       [::]:443 ssl;
    server_name  example.tld;
    root         /var/www/example.tld;

    location /isso {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Script-Name /isso;
        proxy_pass http://localhost:8080;
    }
}
```

```html
<script src="http://example.tld/isso/js/embed.min.js"></script>
<div id="isso-thread"></div>
```

### Isso on a Dedicated Domain

Now, assuming you have your isso instance running on a different URL, such as
`http://example.tld:8080`, but your blog runs on `http://example.tld`:

    ~> cat example.cfg
    [general]
    host = http://example.tld/
    ~> isso -c example.cfg run
     * connecting to SMTP server [failed]
     * connecting to HTTP server [ok]
     * Running on http://localhost:8080/

Make sure, Isso can connect to server that hosts your blog, otherwise you are
not able to post comments.

Integrate Isso with:

```html
<script src="http://example.tld:8080/js/embed.min.js"></script>
<div id="isso-thread"></div>
```

Also, put the plain isso server behind a real web server or [use uWSGI][3].

[3]: https://github.com/posativ/isso/blob/master/docs/uWSGI.md


Website Integration
-------------------

To enable comments, add a `<div id="isso-thread"></div>` or `<section id="isso-thread" ...`
below your post.

To add comment count links to your index page, include `count.min.js` at the
very bottom of your document. All links followed by `#isso-thread`, are
updated with the current comment count.

This functionality is already included when you embed `embed.min.js`, do
*not* mix `embed.min.js` and `count.min.js` in a single document.



Other Documents
---------------

- [Configuration](https://github.com/posativ/isso/blob/master/docs/CONFIGURATION.rst)
- [API overview](https://github.com/posativ/isso/raw/master/docs/API.md)
- [uWSGI usage](https://github.com/posativ/isso/blob/master/docs/uWSGI.md)


Alternatives
------------

- [talkatv](https://github.com/talkatv/talkatv) – Python
- [Juvia](https://github.com/phusion/juvia) – Ruby on Rails
- [Tildehash.com](http://www.tildehash.com/?article=why-im-reinventing-disqus) – PHP
- [SO: Unobtrusive, self-hosted comments](http://stackoverflow.com/q/2053217)
