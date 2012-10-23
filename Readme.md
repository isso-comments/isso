Isso – Ich schrei sonst
=======================

You love static blog generators (especially [Acrylamid][1] \*cough\*) and the only
option to interact with the community is [Disqus][2]. There's nothing wrong with
it, but if you care about the privacy of your audience you should better use
a comment system that is under your control. This is, were Isso comes into play.

[1]: https://github.com/posativ/acrylamid
[2]: http://disqus.com/

Current status: `nosetests specs/`. Ran 11 tests in 0.570s.

## Features/Roadmap

- transparent and lightweight backend (SQLite or plain text files)
- simple JSON API (hence comments are JavaScript-only)
- create comments and modify/delete within a time range
- Ping/Trackback support (not implemented yet)
- simple admin interface (work in progress)
- easy integration, similar to Disqus (work in progress)
- spam filtering using [http:bl](https://www.projecthoneypot.org/) (not implemented yet)

## Installation

TODO

## Migrating from Disqus

Go to [disqus.com](https://disqus.com/) and export your "forum" as XML. If you
use Firefox and you get a 403, try a webkit browser, Disqus did something very
weird with that download link. Next:

    $ isso import /path/to/ur/dump.xml

That's it. Visit your admin page to see all threads. If it doesn't work for you,
please file in a bug report \*including\* your dump.

## API

To fetch all comments for a path, run

    $ curl -H "Accept: application/json" http://example.org/comment/foo-bar/

To write a comment, you have to POST a JSON dictionary with the following key-value
pairs. Text is mandatory otherwise you'll get a 400 Bad Request. You'll also get
a 400 when your JSON is invalid.

Let's say you want to comment on /foo-bar/

    $ curl http://example.org/comment/foo-bar/new -H "Accept: application/json" -X POST -d \
        '{
            "text": "Lorem ipsum ...",
            "name": "Hans", "email": "foo@bla.org", "website": "http://blog/log/"
        }'

This will set a cookie, that expires in a few minutes (15 minutes per default). This
cookie allows you do modify or delete your comment. Don't try to modify that cookie,
it is cryptographically signed. If your cookie is outdated or modified, you'll get
a 403 Forbidden.

For each comment you'll post, you get an unique cookie. Let's try to remove your comment:

    $ curl -H ... -X DELETE http://example.org/comment/foo-bar/1

If your comment has been referenced by another comment, your comment will be cleared but
not deleted to retain depending comments.

## Alternatives

- [Juvia](https://github.com/phusion/juvia) – Ruby on Rails
- [Tildehash.com](http://www.tildehash.com/?article=why-im-reinventing-disqus) – PHP
- [SO: Unobtrusive, self-hosted comments](http://stackoverflow.com/q/2053217)
