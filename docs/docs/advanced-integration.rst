Advanced integration
====================

Comment counter
----------------

If you want to display a comment counter for a given thread, simply
put a link to that comments thread anchor:

.. code-block:: html

    <a href="/my-uri.html#isso-thread">Comments</a>

The *isso js client* willl replace the content of this tag with a human readable
counter like *"5 comments"*.

Alternatively, if guessing from `href` is not relevant, you could use a
`data-isso-id` attribute on the `<a>` to indicate which thread to count for.

Make sure you have `embed.min.js` included in your page (see :doc:`quickstart`).

You can have as many comments counters as you want in a page but be aware that it
implies one `GET` request per counter.
