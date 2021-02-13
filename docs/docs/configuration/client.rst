Client Configuration
====================

You can configure the client (the JS part) with custom data attributes,
preferably in the script tag which embeds the JS:

.. code-block:: html

    <script data-isso="/prefix/"
            data-isso-id="thread-id"
            data-isso-css="true"
            data-isso-lang="ru"
            data-isso-reply-to-self="false"
            data-isso-require-author="false"
            data-isso-require-email="false"
            data-isso-reply-notifications="false"
            data-isso-max-comments-top="10"
            data-isso-max-comments-nested="5"
            data-isso-reveal-on-click="5"
            data-isso-avatar="true"
            data-isso-avatar-bg="#f0f0f0"
            data-isso-avatar-fg="#9abf88 #5698c4 #e279a3 #9163b6 ..."
            data-isso-vote="true"
            data-isso-vote-levels=""
            data-isso-feed="false"
            src="/prefix/js/embed.js"></script>

Furthermore you can override the automatic title detection inside
the embed tag, as well as the thread ID, e.g.:

.. code-block:: html

    <section id="isso-thread" data-title="Foo!" data-isso-id="/path/to/resource"></section>

Additionally, you can override any translation string for any language by adding
a ``data-isso-`` attribute that is equal to the translation key (found `here`__) with
``-text-[lang]`` appended to it. So, for example, if you want to override the
english translation of the ``postbox-notification`` message, you could add:

``data-isso-postbox-notification-text-en="Select to be notified of replies to your comment"``

.. __: https://github.com/posativ/isso/blob/master/isso/js/app/i18n/en.js

Lazy-loading on scroll
----------------------

You can defer loading the ``embed.min.js`` script until the user has scrolled
to the bottom of the page:

.. code-block:: html

    <script type="text/javascript">
        // Lazy-load isso only when page end is in view
        function loadIsso() {
            var script = document.createElement("script");
            script.setAttribute("type", "text/javascript");
            script.setAttribute("src", "/prefix/js/embed.min.js");
            // add relevant data-isso attributes here
            script.setAttribute("data-isso", "/prefix/");
            document.getElementsByTagName("head")[0].appendChild(script);
        }
        let offset = 50; // Start loading 50px before reaching bottom
        function scrollBottomListener(ev) {
            if ((window.scrollY + window.innerHeight)
                    >= (document.documentElement.scrollHeight - offset)) {
                loadIsso();
                window.removeEventListener('scroll', scrollBottomListener);
            }
        }
        window.onload = function() {
          // If viewport >= page height, load immediately
          if ((window.scrollY + window.innerHeight)
                    >= (document.documentElement.scrollHeight - offset)) {
              loadIsso();
          } else {
              window.addEventListener('scroll', scrollBottomListener);
          }
        }
    </script>

*Note that loading additional content only after user interaction is bad for
SEO. Additionally, users could experience a "jank" effect.*

Use lazy-loading only if you are desperately trying to save bandwidth. By
specifying ``async`` in the ``<script`` tag, loading the Isso Javascript will
not render-block anyway.


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

Override useragent's preferred language. Isso has been translated in over 12
languages. The language is configured by its `ISO 639-1
<https://en.wikipedia.org/wiki/ISO_639-1>`_ (two letter) code.

You find a list of all supported languages on `GitHub
<https://github.com/posativ/isso/tree/master/isso/js/app/i18n>`_.

data-isso-reply-to-self
-----------------------

Set to `true` when spam guard is configured with `reply-to-self = true`.

data-isso-require-author
------------------------

Set to `true` when spam guard is configured with `require-author = true`.

data-isso-require-email
-----------------------

Set to `true` when spam guard is configured with `require-email = true`.

data-isso-reply-notifications
-----------------------------

Set to `true` when reply notifications is configured with `reply-notifications = true`.

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

data-isso-gravatar
------------------

Uses gravatar images instead of generating svg images. You have to set
"data-isso-avatar" to **false** when you want to use this. Otherwise
both the gravatar and avatar svg image will show up. Please also set
option "gravatar" to **true** in the server configuration...

data-isso-vote
--------------

Enable or disable voting feature on the client side.

data-isso-vote-levels
---------------------

List of vote levels used to customize comment appearance based on score.
Provide a comma-separated values (eg. `"0,5,10,25,100"`) or a JSON array (eg. `"[-5,5,15]"`).

For example, the value `"-5,5"` will cause each `isso-comment` to be given one of these 3 classes:

- `isso-vote-level-0` for scores lower than `-5`
- `isso-vote-level-1` for scores between `-5` and `4`
- `isso-vote-level-2` for scores of `5` and greater

These classes can then be used to customize the appearance of comments (eg. put a star on popular comments)

data-isso-feed
--------------

Enable or disable the addition of a link to the feed for the comment
thread. The link will only be valid if the appropriate setting, in
``[rss]`` section, is also enabled server-side.
