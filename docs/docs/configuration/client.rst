Client Configuration
====================

You can configure the client (the JS part) with custom data attributes,
preferably in the script tag which embeds the JS:

.. code-block:: html

    <script data-isso="/prefix/"
            data-isso-css="true"
            data-isso-lang="ru"
            data-isso-reply-to-self="false"
            data-isso-require-email="false"
            data-isso-max-comments-top="10"
            data-isso-max-comments-nested="5"
            data-isso-reveal-on-click="5"
            data-isso-avatar="true"
            data-isso-avatar-bg="#f0f0f0"
            data-isso-avatar-fg="#9abf88 #5698c4 #e279a3 #9163b6 ..."
            data-isso-vote="true"
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
english (en), french (fr), italian (it), esperanto (eo), russian (ru) and spanish (es).

data-isso-reply-to-self
-----------------------

Set to `true` when spam guard is configured with `reply-to-self = true`.

data-isso-require-email
-----------------------

Set to `true` when spam guard is configured with `require-email = true`.

data-isso-max-comments-top and data-isso-max-comments-nested
------------------------------------------------------------

Number of top level (or nested) comments to show by default. If some
comments are not shown, an "X Hidden" link is shown.

Set to `"inf"` to show all, or `"0"` to hide all.

data-isso-reveal-on-click
-------------------------

Number of comments to reveal on clicking the "X Hidden" link.

data-isso-avatar
----------------

Enable or disable avatar generation.

data-isso-avatar-bg
-------------------

Set avatar background color. Any valid CSS color will do.

data-isso-avatar-fg
-------------------

Set avatar foreground color. Up to 8 colors are possible. The default color
scheme is based in `this color palette <http://colrd.com/palette/19308/>`_.
Multiple colors must be separated by space. If you use less than eight colors
and not a multiple of 2, the color distribution is not even.

data-isso-vote
--------------

Enable or disable voting feature on the client side.

data-isso-id
------------

Broken – do not use. https://github.com/posativ/isso/issues/27

Set a custom thread id, defaults to current URI. If you a comment counter, add
this attribute to the link tag, too.

.. code-block:: html

    <section data-isso-id="test.abc" id="isso-thread"></section>
