Client Configuration
====================

You can configure the client (the JS part) with custom data attributes,
preferably in the script tag which embeds the JS:

.. code-block:: html

    <script data-isso="/prefix/"
            data-isso-css="true"
            data-isso-lang="ru"
            data-isso-reply-toself="false"
            src="/prefix/js/embed.js"></script>

Furthermore you can override the automatic title detection inside
the embed tag, e.g.:

.. code-block:: html

    <section id="isso-thread" data-title="Foo!"></section>

data-isso
---------

Isso usually detects the REST API automatically, but when you serve the JS
script on a different location, this may fail. Use `data-isso` to
override the API location:

.. code-block:: html

    <script data-isso="/isso" src="/path/to/embed.min.js"></script>

data-isso-css
-------------

Set to `false` prevents Isso from automatically appending the stylesheet.
Defaults to `true`.

.. code-block:: html

    <script src="..." data-isso-css="false"></script>

data-isso-lang
--------------

Override useragent's preferred language. Currently available: german (de),
english (en) and french (fr).

data-isso-reply-to-self
-----------------------

Set to `true` when spam guard is configured with `reply-to-self = true`.

data-isso-id
------------

Set a custom thread id, defaults to current URI. If you a comment counter, add
this attribute to the link tag, too.

.. code-block:: html

    <section data-isso-id="test.abc" id="isso-thread"></section>
