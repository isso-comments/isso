Tips & Tricks
=============


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

.. _advanced-migration:

Advanced Migration
------------------

In quickstart we saw you can import comments from Disqus or WordPress. But there
are a many other comments system and you could be using one of them.

Isso provides a way to import such comments, however it's up to you to to:

- dump comments
- fit the data to the following JSON format::

    A list of threads, each item being a dict with the following data:

    - id: a text representing the unique thread id (note: by default isso
          associates this ID to the article URL, but it can be changed on
          client side with "data-isso-id" - see :doc:`client configuration <../configuration/client>` )
    - title: the title of the thread
    - comments: the list of comments

        Each item in that list of comments is a dict with the following data:

        - id: an integer with the unique id of the comment inside the thread
          (it can be repeated among different threads); this will be used to
          order the comment inside the thread
        - author: the author's name
        - email: the author's email
        - website: the author's website
        - remote_addr: the author's IP
        - created: a timestamp, in the format "%Y-%m-%d %H:%M:%S"

Example:

.. code-block:: json

    [
        {
            "id": "/blog/article1",
            "title": "First article!",
            "comments": [
                {
                    "author": "James",
                    "created": "2018-11-28 17:24:23",
                    "email": "email@mail.com",
                    "id": "1",
                    "remote_addr": "127.0.0.1",
                    "text": "Great article!",
                    "website": "http://fefzfzef.frzr"
                },
                {
                    "author": "Harold",
                    "created": "2018-11-28 17:58:03",
                    "email": "email2@mail.com",
                    "id": "2",
                    "remote_addr": "",
                    "text": "I hated it...",
                    "website": ""
                }
            ]
        }
    ]

Keep in mind that isso expects to have an array, so keep the opening and ending square bracket even if you have only one article thread!

Next you can import you json dump:

.. code-block:: sh

    ~> isso -c /path/to/isso.cfg import -t generic comment-dump.json
    [100%]  53 threads, 192 comments


Pretty-print entire comments database
-------------------------------------

.. Migration complete from https://github.com/posativ/isso/wiki/Tips-&-tricks

The following bash function pretty-print the entire comments DB sorted by
insertion date.

.. code-block:: bash

   get_blog_comments () {
       ssh $host sqlite3 -line /path/to/isso/isso.db \
           "'SELECT t.uri,c.created,c.modified,c.text,c.author,c.email,c.website \
             FROM comments AS c, threads as t WHERE c.tid = t.id;'" \
           | perl -wpe '/(created|modified) = ./&&s/= (.*)/"= ".scalar(localtime($1))/e';
   }

Example output:

.. code-block:: text

        uri = /lucas/blog/2014/12/12/fr-la-tete-dans-le-guidon/
    created = Mon Dec 15 13:10:28 2014
   modified =
       text = Merci ! Je suis très content d'apprendre que cette lecture a pu plaire à quelqu'un
   N'hésitez pas à partager vos propres réflexions et astuces dans les commentaires.
     author = lucas
      email = lucas@chezsoi.org
    website = https://chezsoi.org/lucas/blog


Delete IP addresses weekly
--------------------------

Add this to your ``crontab`` to set all saved commenter IP addresses to
``127.0.0.1`` to preserve their privacy under GDPR:

.. code-block:: text

   @weekly /usr/bin/sqlite3 /path/to/isso/comments.db 'UPDATE comments SET remote_addr = "127.0.0.1";'

From `blog.mdosch.de <https://blog.mdosch.de/2018/05/20/isso-ip-adressen-woechentlich-loeschen/>`_:

*Note that Isso already anonymizes the last part of IP addresses by setting
them to to zero.*


.. attention::

   This section of the Isso documentation is incomplete. Please help by expanding it.

   Click the ``Edit on GitHub`` button in the top right corner and read the
   GitHub Issue named
   `Improve & Expand Documentation <https://github.com/posativ/isso/issues/797>`_
   for further information.

   **What's missing?**

   - Removing unused languages
   - Importing & exporting comments (integrate migration docs)
   - Keeping compat using babel

   ... and other collected tips & tricks, maybe also from the wiki.
