Isso API
========

The Isso API uses HTTP and JSON as primary communication protocol.


## JSON format

When querying the API you either get an error, an object or list of objects
representing the comment. Here's a example JSON returned from Isso:

```json
{
    "text": "Hello, World!",
    "author": "Bernd",
    "website": null,
    "votes": 0,
    "mode": 1,
    "id": 1,
    "parent": null,
    "hash": "68b329da9893e34099c7d8ad5cb9c940",
    "created": 1379001637.50,
    "modified": null
}
```

text
: required, comment as HTML

author
: author's name, may be `null`

website
: author's website, may be `null`

votes
: sum of up- and downvotes, defaults to zero.

mode
: * 1, accepted comment
  * 2, comment in moderation queue
  * 4, comment deleted, but is referenced

id
: unique comment number per thread

parent
: answer to a parent id, may be `null`

hash
: user identification, used to generate identicons

created
: time in seconds sinde epoch

modified
: last modification time in seconds, may be `null`


## List comments

List all visible comments for a thread. Does not include deleted and
comments currently in moderation queue.

    GET /?uri=path

You must encode `path`, e.g. to retrieve comments for `/hello-world/`:

    GET /?uri=%2Fhello-world%2F

To disable automatic Markdown-to-HTML conversion, pass `plain=1` to the
query URL:

    GET /?uri=...&plain=1

As response, you either get 200, 400, or 404, which are pretty self-explanatory.

    GET /
    400 BAD REQUEST

    GET /?uri=%2Fhello-world%2F
    404 NOT FOUND

    GET /?uri=%2Fcomment-me%2F
    [{comment 1}, {comment 2}, ...]


## Create comments

...


## Delete comments

...


## Up- and downvote comments

...
