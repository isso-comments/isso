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
- simple admin interface (not implemented yet)
- easy integration, similar to Disqus (not implemented yet)
- spam filtering using [http:bl](https://www.projecthoneypot.org/) (not implemented yet)

## Installation

TODO

## API

### fetch comments for /foo-bar/

    $ curl -H "Accept: application/json" http://example.org/comment/foo-bar/

### comment at /foo-bar/

    $ curl -H "Accept: application/json" -X POST -d \
        '{
            "text": "Lorem ipsum ...",

            # optional
            "name": "Hans", "email": "foo@bla.org", "website": "http://blog/log/"
        }' http://example.org/comment/foo-bar/new

### modify 12. comment at /foo-bar/

    $ curl -H "Accept: application/json" -X PUT -d ... http://example.org/comment/foo-bar/12

You can only modify your own comment in a given time range (defaults to 15 minutes).

### delete 2nd comment at /foo-bar/

    $ curl -H ... -X DELETE http://example.org/comment/foo-bar/2

You can only delete your own comment in a given time range (defaults to 15 minutes). If
your comment has been referenced by another comment, your comment will be cleared but not
deleted to maintain depending comments.

## Alternatives

- [Juvia](https://github.com/phusion/juvia) – Ruby on Rails
- [Tildehash.com](http://www.tildehash.com/?article=why-im-reinventing-disqus) – PHP
- [SO: Unobtrusive, self-hosted comments](http://stackoverflow.com/q/2053217)
