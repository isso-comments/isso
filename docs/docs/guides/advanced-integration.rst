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

You can have as many comments counters as you want in a page, and they will be
merged into a single `GET` request.

Asynchronous comments loading
-----------------------------

Isso will automatically fetch comments after `DOMContentLoaded` event. However
in the case where your website is creating content dynamically (eg. via ajax),
you need to re-fetch comment thread manually. Here is how you can re-fetch the
comment thread:

.. code-block:: js

    window.Isso.fetchComments()

It will delete all comments under the thread but not the PostBox, fetch
comments with `data-isso-id` attribute of the element `section#isso-thread` (if
that attribute does not exist, fallback to `window.location.pathname`), then
fill comments into the thread. In other words, you should change `data-isso-id`
attribute of the element `section#isso-thread` (or modify the pathname with
`location.pushState`) before you can get new comments. And the thread element
itself should *NOT* be touched or removed.

If you removed the `section#isso-thread` element, just create another element
with same TagName and ID in which you wish comments to be placed, then call the
`init` method of `Isso`:

.. code-block:: js

    window.Isso.init()

Then Isso will initialize the comment section and fetch comments, as if the page
was loaded.
