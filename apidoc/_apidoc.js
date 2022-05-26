// ------------------------------------------------------------------------------------------
// History.
// ------------------------------------------------------------------------------------------
/**
* @api {get} /count (Deprecated) Count for single thread
* @apiGroup Thread
* @apiName count
* @apiVersion 0.12.6
* @apiDeprecated use (#Thread:counts) instead.
* @apiDescription
*     (Deprecated) Counts the number of comments for a single thread.

* @apiBody {Number[]} urls
*     Array of URLs for which to fetch comment counts

* @apiExample {curl} Get the respective counts of 5 threads:
*     curl 'https://comments.example.com/count' -d '["/blog/firstPost.html", "/blog/controversalPost.html", "/blog/howToCode.html", "/blog/boringPost.html", "/blog/isso.html"]

* @apiSuccessExample {json} Counts of 5 threads:
*     [2, 18, 4, 0, 3]
*/

/**
* @api {post} /new create new
* @apiGroup Comment
* @apiName new
* @apiVersion 0.12.6
* @apiDescription
*     Creates a new comment. The server issues a cookie per new comment which acts as
*     an authentication token to modify or delete the comment.
*     The token is cryptographically signed and expires automatically after 900 seconds (=15min) by default.
* @apiUse csrf

* @apiQuery {String} uri
*     The uri of the thread to create the comment on.
* @apiBody {String{3..}} text
*     The comment’s raw text.
* @apiBody {String} [author]
*     The comment’s author’s name.
* @apiBody {String} [email]
*     The comment’s author’s email address.
* @apiBody {String} [website]
*     The comment’s author’s website’s url.
* @apiBody {number} [parent]
*     The parent comment’s id if the new comment is a response to an existing comment.

* @apiExample {curl} Create a reply to comment with id 15:
*     curl 'https://comments.example.com/new?uri=/thread/' -d '{"text": "Stop saying that! *isso*!", "author": "Max Rant", "email": "rant@example.com", "parent": 15}' -H 'Content-Type: application/json' -c cookie.txt

* @apiUse commentResponse

* @apiSuccessExample {json} Success after the above request:
*     HTTP/1.1 201 CREATED
*     Set-Cookie: 1=...; Expires=Wed, 18-Dec-2013 12:57:20 GMT; Max-Age=900; Path=/
*     X-Set-Cookie: isso-1=...; Expires=Wed, 18-Dec-2013 12:57:20 GMT; Max-Age=900; Path=/
*     {
*         "website": null,
*         "author": "Max Rant",
*         "parent": 15,
*         "created": 1464940838.254393,
*         "text": "&lt;p&gt;Stop saying that! &lt;em&gt;isso&lt;/em&gt;!&lt;/p&gt;",
*         "dislikes": 0,
*         "modified": null,
*         "mode": 1,
*         "hash": "e644f6ee43c0",
*         "id": 23,
*         "likes": 0
*     }
*/
