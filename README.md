Isso – Ich schrei sonst
=======================

You love static blog generators (especially [Acrylamid][1] *cough*) and the
only option to interact with the community is [Disqus][2]. There's nothing
wrong with it, but if you care about the privacy of your audience you are
better off with a comment system that is under your control. This is, were
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
- simple admin interface
- spam filtering


Installation
------------

Requirements:

- Python 2.6 or 2.7
- [NPM](https://npmjs.org/) and [Bower](http://bower.io/)

On Debian/Ubuntu install the following packages

    ~> sudo aptitude install python-setuptools python-dev npm 
    ~> ln -s /usr/bin/nodejs /usr/bin/node 

For now (as long as there is no stable version), you need to manually
build everything:

    ~> git clone https://github.com/posativ/isso.git
    ~> cd isso/
    ~> python setup.py develop

To fetch the requires JS components, run:

    ~> cd isso/js/
    ~> bower install almond q requirejs requirejs-domready requirejs-text

You can now either use the JS client as-is (using [require.js][r.js], see
below) or compile all JS into a single file:

    ~> cd isso/js
    ~> npm install -g requirejs uglifyjs
    ~> r.js -o build.embed.js
    ~> r.js -o build.count.js

At last, you need to build the CSS:

    ~> cd ../css
    ~> gem install sass
    ~> scss isso.scss > isso.css

Before you start, you may want to import comments from
[Disqus.com](https://disqus.com/):

    ~> isso import ~/Downloads/user-2013-09-02T11_39_22.971478-all.xml
    [100%]  53 threads, 192 comments

You start the server via (try to visit [http://localhost:8080/static/post.html]()).

    ~> isso run


Webserver Configuration
-----------------------

This part is not fun, I know. I have prepared two possible setups for nginx,
using Isso on the same domain as the blog, and on a different domain. Each
setup has its own benefits.

### Isso on a Sub URI

Let's assume you want Isso on `/isso`, use the following nginx snippet

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

The Isso API endpoint is now `example.tld/isso`, check by `curl`ing the client
JS located at `http://example.tld/isso/js/embed.js`.

### Isso on a Dedicated Domain

...


Website Integration
-------------------

Add the following two lines into your HTML header:

```html
<link rel="stylesheet" href="http://example.tld/isso/static/isso.css" />
<script src="http://example.tld/isso/js/embed.min.js"></script>
```

To enable comments, add a `<div id="#isso-thread"></div>` below your post and
let the magic happen :-)

To add comment count links to your index page, include `count.min.js` at the
very bottom of your document. All links followed by `#isso-thread`, are
updated with the current comment count.

This functionality is already included when you embed `embed.min.js`, do
*not* mix `embed.min.js` and `count.min.js` in a single document.

### Embed with require.js

This section is primarily for developers: The client-side JS is modularized
and uses an AMD loader for execution. You can easily hack on the JS files,
when using [require.js][r.js]:

```html
<link rel="stylesheet" href="/isso/static/isso.css" />
<script src="/isso/js/config.js"></script>
<script data-main="/isso/js/embed" src="/isso/js/components/requirejs/require.js"></script>
```


API
---

See [docs/API.md](https://github.com/posativ/isso/blob/master/docs/API.md).


Alternatives
------------

- [talkatv](https://github.com/talkatv/talkatv) – Python
- [Juvia](https://github.com/phusion/juvia) – Ruby on Rails
- [Tildehash.com](http://www.tildehash.com/?article=why-im-reinventing-disqus) – PHP
- [SO: Unobtrusive, self-hosted comments](http://stackoverflow.com/q/2053217)


[r.js]: http://require.js/
