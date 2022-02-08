API
====

The Isso API uses HTTP and JSON as primary communication protocol.

.. contents::
    :local:


JSON format
-----------

When querying the API you either get a regular HTTP error, an object or list of
objects representing the comment. Here's an example JSON returned from
Isso:

.. code-block:: json

    {
        "id": 1,
        "parent": null,
        "text": "<p>Hello, World!</p>\n",
        "mode": 1,
        "hash": "4505c1eeda98",
        "author": null,
        "website": null,
        "created": 1387321261.572392,
        "modified": null,
        "likes": 3,
        "dislikes": 0
    }

id :
    comment id (unique per website).

parent :
    parent id reference, may be ``null``.

text :
    required, comment written in Markdown.

mode :
    * 1 – accepted
    * 2 – in moderation queue
    * 4 – deleted, but referenced.

hash :
    user identication, used to generate identicons. PBKDF2 from email or IP
    address (fallback).

author :
    author's name, may be ``null``.

website :
    author's website, may be ``null``.

likes :
    upvote count, defaults to 0.

dislikes :
    downvote count, defaults to 0.

created :
    time in seconds since UNIX time.

modified :
    last modification since UNIX time, may be ``null``.


List comments
-------------

List all publicly visible comments for thread `uri`:

.. code-block:: text

    GET /?uri=%2Fhello-world%2F

uri :
    URI to fetch comments for, required.

plain :
    pass plain=1 to get the raw comment text, defaults to 0.


Get the latest N comments for all threads:

.. code-block:: text

    GET /latest?limit=N

The N parameter limits how many of the latest comments to retrieve; it's
mandatory, and must be an integer greater than 0.

This endpoint needs to be enabled in the configuration (see the
``latest-enabled`` option in the ``general`` section).


Create comment
--------------

To create a new comment, you need to issue a POST request to ``/new`` and add
the current URI (so the server can check if the location actually exists).

.. code-block:: bash

    $ curl -vX POST http://isso/new?uri=%2F -d '{"text": "Hello, World!"}' -H "Content-Type: application/json"
    < HTTP/1.1 201 CREATED
    < Set-Cookie: 1=...; Expires=Wed, 18-Dec-2013 12:57:20 GMT; Max-Age=900; Path=/
    {
        "author": null,
        "created": 1387370540.733824,
        "dislikes": 0,
        "email": null,
        "hash": "6dcdbfb4f00d",
        "id": 1,
        "likes": 0,
        "mode": 1,
        "modified": null,
        "parent": null,
        "text": "<p>Hello, World!</p>\n",
        "website": null
    }

The payload must be valid JSON. To prevent CSRF attacks, you must set the
`Content-Type` to `application/json` or omit the header completely.

The server issues a cookie per new comment which acts as authentication token
to modify or delete your own comment. The token is cryptographically signed
and expires automatically after 900 seconds by default.

The following keys can be used to POST a new comment, all other fields are
dropped or replaced with values from the server:

text : String
    Actual comment, at least three characters long, required.

author : String
    Comment author, optional.

website : String
    Commenter's website (currently no field available in the client JS though),
    optional.

email : String
    Commenter's email address (can be any arbitrary string though) used to
    generate the identicon. Limited to 254 characters (RFC specification),
    optional.

parent : Integer
    Reference to parent comment, optional.


Edit comment
------------

When your authentication token is not yet expired, you can issue a PUT request
to update `text`, `author` and `website`. After an update, you get an updated
authentication token and the comment as JSON:

.. code-block:: bash

    $ curl -X PUT http://isso/id/1 -d "..." -H "Content-Type: application/json"


Delete comment
--------------

You can delete your own comments when your authentication token (= cookie) is
not yet expired:

.. code-block:: bash

    $ curl -X DELETE http://isso/id/1 -H "Content-Type: application/json"
    null

Returns either `null` or a comment with an empty text value when the comment
is still referenced by other comments.


Up- and downvote comments
-------------------------

...

Get comment count
-----------------

Counts all publicly visible comments for thread `uri`:

.. code-block:: text

    GET /count?uri=%2Fhello-world%2F
    2

uri :
    URI to count comments for, required.

returns an integer

Get Atom feed
-------------

Get an Atom feed of comments for thread `uri`:

.. code-block:: text

    GET /feed?uri=%2Fhello-world%2F

uri :
    URI to get comments for, required.

Returns an XML document as the Atom feed.
