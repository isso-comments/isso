Frequently asked question
=========================

Why not use Gravatar/Libravatar/... ?
-------------------------------------

Various people asked or complained about the generated icons next to their
comments. First, it is not an avatar, it is an identicon used to
*identify* an author of multiple comments without leaking personal
informations (unlike Gravatar).

If you are in need of Gravatar_, then use Disqus. If you run your own
Libravatar_ server, you can work on a patch for Isso which adds *optional*
support for avatars.

.. _Gravatar: https://secure.gravatar.com/
.. _Libravatar: http://libravatar.org/

Why SQLite3?
------------

Although partially answered on the index page, here a more complete answer: If
you manage massive amounts of comments, Isso is a really bad choice. Isso is
designed to be simple and easy to setup, not optimizied for high-traffic
websites (use a `dedicated Disqus`_ instance then).

    comments are not big data

For example, 209 threads and 778 comments in total only need 620K (kilobyte)
memory. Excellent use case for SQLite.

.. _dedicated Disqus:
