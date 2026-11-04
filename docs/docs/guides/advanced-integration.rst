Advanced integration
====================

Comment counter
---------------

If you want to display a comment counter for a given thread, simply
put a link to that comments thread anchor:

.. code-block:: html

    <a href="/my-uri.html#isso-thread">Comments</a>

The *isso js client* will replace the content of this tag with a human readable
counter like *"5 comments"*.

Alternatively, if guessing from `href` is not relevant, you could use a
`data-isso-id` attribute on the `<a>` to indicate which thread to count for.

Now, either include `count.min.js` if you want to show only the comment count
(e.g. on an index page) or `embed.min.js` for the full comment client (see
:doc:`quickstart`); do not mix both.

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

.. _reacting-to-rendered-comments:

Reacting to rendered comments
-----------------------------

.. versionadded:: 0.14.1

Isso dispatches DOM events after it renders parts of the widget, so that you can
manipulate the generated markup from your own JavaScript, for example to add
CSS framework classes without overriding Isso's stylesheet.

All events bubble and are dispatched on the ``#isso-thread`` element, so you may
listen on ``#isso-thread`` or on ``document``. Each event's ``detail.element``
is the DOM node that was just rendered.

.. list-table::
   :header-rows: 1
   :widths: 30 40 30

   * - Event
     - Fired when
     - ``event.detail``
   * - ``isso-postbox-rendered``
     - A comment form (the main postbox and every reply form) has been built.
       The element is not attached to the document yet at this point.
     - ``{ element, parent }``: ``parent`` is the id of the comment being
       replied to, or ``null`` for the main postbox.
   * - ``isso-comment-rendered``
     - A comment has been inserted into the thread (initial load, newly posted
       comment, replies, and comments revealed via the "N Hidden" link).
     - ``{ element, comment }`` — ``comment`` is the comment object returned by
       the API.
   * - ``isso-thread-rendered``
     - ``fetchComments()`` has finished (or failed). Fires with ``count: 0``
       when there are no comments, and also on the error path (when the API
       request fails) with ``count: 0`` and ``detail.error`` set.
     - ``{ element, count[, error] }`` — ``element`` is ``#isso-thread``,
       ``count`` is the number of top-level comments in the thread (the API's
       ``total_replies``); it excludes nested replies and any not-yet-loaded
       comments behind the "N Hidden" link. ``error`` is present only when the
       fetch failed and holds the rejection reason.

Example: give the postbox buttons Bootstrap classes and log rendered comments:

.. code-block:: js

    document.addEventListener('isso-postbox-rendered', function (e) {
        e.detail.element.querySelector(".isso-postbox-submit")
            .classList.add('btn', 'btn-primary');
        e.detail.element.querySelector(".isso-postbox-preview")
            .classList.add('btn', 'btn-secondary');
    });

    document.addEventListener('isso-comment-rendered', function (e) {
        console.log('rendered comment', e.detail.comment.id, e.detail.element);
    });

Place the listeners before ``embed.min.js`` runs (or before calling
``window.Isso.init()``) so that they are registered when the first elements are
rendered.

The postbox buttons also carry dedicated classes
(``isso-postbox-submit``, ``isso-postbox-preview`` and ``isso-postbox-edit``)
that you can target directly from CSS or from an event listener.
