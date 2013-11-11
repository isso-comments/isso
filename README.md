Isso – Ich schrei sonst
=======================

You love static blog generators (especially [Acrylamid][1] *cough*) and the
only option to interact with your community is [Disqus][2]. There's nothing
wrong with it, but if you care about the privacy of your audience you are
better off with a comment system that is under your control. This is, where
Isso comes into play.

[1]: https://github.com/posativ/acrylamid
[2]: https://disqus.com/

**[Try Yourself!](http://posativ.org/isso/)**


Features
--------

* [CRUD](https://en.wikipedia.org/wiki/Create,_read,_update_and_delete) comments written in Markdown
* SQLite backend, Disqus import
* client-side JS (currently 54kb minified, 18kb gzipped)
* I18N, available in german and english (also fallback)


Installation
------------

- Python 2.6, 2.7 or 3.3
- a working C compiler

Install Isso with:

    ~> pip install isso

Set your database location and website:

    ~> cat my.cfg
    [general]
    dbpath = /var/lib/isso/comments.db
    host = http://example.tld/

Optional: you can import your comments from [Disqus.com](https://disqus.com/):

    ~> isso -c my.cfg import ~/Downloads/user-2013-09-02T11_39_22.971478-all.xml
    [100%]  53 threads, 192 comments

Now start the server:

    ~> isso -c my.cfg run
    2013-10-30 09:32:48,369 WARNING: unable to connect to SMTP server
    2013-10-30 09:32:48,408 INFO: connected to HTTP server

Make sure, Isso can connect to the server that hosts your blog, otherwise you
are not able to post comments.


Website Integration
-------------------

You can run Isso on a dedicated domain or behind a sub URI like `/isso`. It
makes actually no difference except for the webserver configuration (see
below).

Whatever method you prefer (just change the URL), to embed comments add

```html
<script src="http://example.tld/js/embed.min.js"></script>
```

to your HTML (presumedly into `<head>`) and

```html
<div id="isso-thread"></div>
```

below your post. That's all. The JavaScript client will automatically detect
the API endpoint.

To show the comment count for posts (but no comments), add

```html
<script src="http://example.tld/js/count.min.js"></script>
```

to your header and all links ending with `#isso-thread` are updated with the
current comment count.

This functionality is already included when you embed `embed.min.js`, do
*not* mix `embed.min.js` and `count.min.js` in a single document.

### Client Configuration

You can configure the client (the JS part) via `data-` attributes:

*   data-title

    When you start a new thread (= first comment on a page), Isso sends
    a GET request that page to see if it a) exists and b) parse the site's
    heading (currently used as subject in emails).

    Isso assumes that the title is inside an `h1` tag near the isso thread:

    ```html
    <html>
        <body>
            <h1>Website Title</h1>
            <article>
                <header>
                    <h1>Post Title</h1>
                <section id="isso-thread">
            ...
    ```

    In this example, the detected title is `Post Title` as expected, but some
    older sites may only use a  single `h1` as their website's maintitle, and
    a `h2` for the post title. Unfortunately this is unambiguous and you have
    to tell Isso what's the actual post title:

    ```html
    <section data-title="Post Title" id="isso-thread">
    ```

    Make sure to escape the attribute value.

*   data-isso

    Isso usually detects the REST API automatically, but when you serve the JS
    script on a different location, this may fail. Use `data-isso` to
    override the API location:

     ```html
     <script data-isso="/isso" src="/path/to/embed.min.js"></script>
     ```

*   data-isso-css

    Set to `false` prevents Isso from automatically appending the stylesheet.
    Defaults to `true`.

    ```html
    <script src="..." data-isso-css="false"></script>
    ```

### Webserver configuration

*   nginx configuration to run Isso on `/isso`:

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

*   nginx configuration to run Isso on a dedicated domain:

    ```nginx
    server {
        listen       [::]:8080;
        server_name  comments.example.tld;

        location / {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_pass http://localhost:8080;
        }
    }
    ```


Documentation
-------------

- [Configuration](https://github.com/posativ/isso/blob/master/docs/CONFIGURATION.rst)
- [uWSGI](https://github.com/posativ/isso/blob/master/docs/uWSGI.md)
- [Contributing](https://github.com/posativ/isso/blob/master/CONTRIBUTING.md)
- [Development](https://github.com/posativ/isso/blob/master/docs/DEVELOPMENT.md)
- [API overview](https://github.com/posativ/isso/raw/master/docs/API.md)

For further help, join `#isso` on Freenode!


Alternatives
------------

- [talkatv](https://github.com/talkatv/talkatv) – Python
- [Juvia](https://github.com/phusion/juvia) – Ruby on Rails
- [Tildehash.com](http://www.tildehash.com/?article=why-im-reinventing-disqus) – PHP
- [SO: Unobtrusive, self-hosted comments](http://stackoverflow.com/q/2053217)
