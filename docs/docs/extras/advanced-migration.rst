Advanced Migration
==================

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

