Frequently asked question
=========================

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
