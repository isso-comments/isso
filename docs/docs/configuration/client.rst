Client Configuration
====================

You can configure the client (the JS part) with custom data attributes,
preferably in the script tag which embeds the JS:

.. code-block:: html

    <script data-isso="/prefix/"
            data-isso-css="true"
            data-isso-lang="ru"
            data-isso-reply-to-self="false"
            data-avatar-bg="#f0f0f0"
            data-avatar-fg="#9abf88 #5698c4 #e279a3 #9163b6 ..."
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
english (en), french (fr), italian (it) and russian (ru).

data-isso-reply-to-self
-----------------------

Set to `true` when spam guard is configured with `reply-to-self = true`.

data-isso-avatar-bg
-------------------

Set avatar background color. Any valid CSS color will do.

data-isso-avatar-fg
-------------------

Set avatar foreground color. Up to 8 colors are possible. The default color
scheme is based in `this color palette <http://colrd.com/palette/19308/>`_.
Multiple colors must be separated by space. If you use less than eight colors
and not a multiple of 2, the color distribution is not even.

data-isso-id
------------

Broken – do not use. https://github.com/posativ/isso/issues/27

Set a custom thread id, defaults to current URI. If you a comment counter, add
this attribute to the link tag, too.

.. code-block:: html

    <section data-isso-id="test.abc" id="isso-thread"></section>
