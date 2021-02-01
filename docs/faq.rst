Frequently asked question
=========================

Why SQLite3?
------------

Although partially answered on the index page, here is a more complete answer: If
you manage massive amounts of comments, Isso is a really bad choice. Isso is
designed to be simple and easy to setup, it is not optimized for high-traffic
websites.

    Comments are not big data.

For example, if you have 209 threads and 778 comments in total this only needs 620 kilobytes
of memory. This is an excellent use case for SQLite.
