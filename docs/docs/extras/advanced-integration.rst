Advanced integration
====================

Comment counter
---------------

If you want to display a comment counter for a given thread, simply
put a link to that comments thread anchor:

.. code-block:: html

    <a href="/my-uri.html#isso-thread">Comments</a>

The *isso js client* willl replace the content of this tag with a human readable
counter like *"5 comments"*.

Alternatively, if guessing from `href` is not relevant, you could use a
`data-isso-id` attribute on the `<a>` to indicate which thread to count for.

Now, either include `count.min.js` if you want to show only the comment count
(e.g. on an index page) or `embed.min.js` for the full comment client (see
:doc:`../quickstart`); do not mix both.

You can have as many comments counters as you want in a page but be aware that it
implies one `GET` request per comment anchor.
