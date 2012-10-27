/* Isso – Ich schrei sonst!
 *
 * Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 *
 *
 * Code requires Bean, Bonzo, Qwery, domReady (all are part of jeesh) and
 * reqwest. To ease integration with websites, all classes are prefixed
 * with `isso`.
 */


/* utility functions -- JS Y U SO STUPID?
 *
 * read(cookie): return `cookie` string if set
 * zfill(argument, i): zero fill `argument` with `i` zeros
 */


function read(cookie){
    return(document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2]
};


function format(date){
    /*!
     * JavaScript Pretty Date
     * Copyright (c) 2011 John Resig (ejohn.org)
     * Licensed under the MIT and GPL licenses.
     */
    var diff = (((new Date()).getTime() - date.getTime()) / 1000),
        day_diff = Math.floor(diff / 86400);

    if ( isNaN(day_diff) || day_diff < 0 || day_diff >= 31 )
        return;

    return day_diff == 0 && (
            diff < 60 && "just now" ||
            diff < 120 && "1 minute ago" ||
            diff < 3600 && Math.floor( diff / 60 ) + " minutes ago" ||
            diff < 7200 && "1 hour ago" ||
            diff < 86400 && Math.floor( diff / 3600 ) + " hours ago") ||
        day_diff == 1 && "Yesterday" ||
        day_diff < 7 && day_diff + " days ago" ||
        day_diff < 31 && Math.ceil( day_diff / 7 ) + " weeks ago";
}

/*
 * isso specific helpers to create, modify, delete and receive comments
 */

function verify(data) {
    return data['text'] == null ? false : true
};


function create(data, func) {

    if (!verify(data)) {
        return;
    }

    $.ajax('POST', '/1.0/' + encodeURIComponent(window.location.pathname) + '/new',
        JSON.stringify(data), {'Content-Type': 'application/json'}).then(func);
};


function modify(id, data, func) {
    if (!verify(data)) {
        return;
    }

    $.ajax('PUT', '/1.0/' + encodeURIComponent(window.location.pathname) + '/' + id,
    JSON.stringify(data), {'Content-Type': 'application/json'}).then(func)
};


function form(id, appendfunc, eventfunc) {
    /*
    Returns HTML for form and registers submit call.

    Synopsis: `isso_N` is the comment with the id N. `issoform` is a new
    form to write an answer to the article or answer to a comment using
    `issoform_N` where N is the id to respond to.

    :param id: comment id
    :param returnfunc: function, that takes one argument (the HTML to display the form)
    :param eventfunc: function, when the user submits the form
    */

    var formid = 'issoform' + (id ? ('_' + id) : ''), form =
    '<div class="issoform" id="' + formid + '">' +
        '<div>' +
        '    <input type="text" name="name" id="author" value="" placeholder="Name">' +
        '</div>' +
        '<div>' +
        '    <input type="email" name="email" id="email" value="" placeholder="Email">' +
        '</div>' +
        '<div>' +
            '<input type="url" name="website" id="website" value="" placeholder="Website URL">' +
        '</div>' +
        '<div>' +
        '    <textarea rows="10" name="comment" id="comment" placeholder="Comment"></textarea>' +
        '</div>' +
        '<div>' +
            '<input type="submit" name="submit" value="Add Comment">' +
        '</div>' +
    '</div>'

    appendfunc(form);
    $('#' + formid + ' ' + 'input[type="submit"]').on('click', eventfunc);
};


function update(post) {

    var node = $('#isso_' + post['id']);
    $('div.text', node).html(post['text']);
};


function insert(post) {
    /*
    Insert a comment into #isso_thread.

    :param post: JSON from API call
    */

    var path = encodeURIComponent(window.location.pathname);
    var author = post['author'] || 'Anonymous';

    if (post['website']) {
        author = '<a href="' + post['website'] + '" rel="nofollow">' + author + '</a>';
    }

    var date = new Date(parseInt(post['created']) * 1000);

    // create <ul /> for parent, if used
    if (post['parent']) {
        $('#isso_' + post['parent']).append('<ul></ul>');
    }

    $(post['parent'] ? '#isso_' + post['parent'] + ' > ul:last-child' : '#isso_thread > ul').append(
        '<article class="isso" id="isso_' + post['id'] + '">' +
        '  <header><span class="author">' + author + '</span>' +
        '  </header>' +
        '  <div class="text">' + post['text'] +
        '  </div>' +
        '  <footer>' +
        '    <a href="#">Antworten</a>' +
        '    <a href="#isso_' + post['id'] + '">#' + post['id'] + '</a>' +
        '    <time datetime="' + date.getUTCFullYear() + '-' + date.getUTCMonth() + '-' +  date.getUTCDate() + '">' + format(date) +
        '    </time>' +
        '  </footer>' +
        '</article>');

    if (read('session-' + path + '-' + post['id'])) {
        $('#isso_' + post['id'] + '> footer > a:first-child')
            .after('<a class="delete" href="#">Löschen</a>')
            .after('<a class="edit" href="#">Bearbeiten</a>');

        // DELETE
        $('#isso_' + post['id'] + ' > footer .delete').on('click', function(event) {
            $.ajax('DELETE', '/1.0/' + path + '/' + post['id']).then(function(status, rv) {
                // XXX comment might not actually deleted
                $('#isso_' + post['id']).remove();
            });
            event.stop();
        });

        // EDIT
        $('#isso_' + post['id'] + ' > footer .edit').on('click', function(event) {

            if ($('#issoform_' + post['id']).length == 0) {

                $.ajax('GET', '/1.0/' + path + '/' + post['id'], {'plain': '1'})
                 .then(function(status, rv) {
                    rv = JSON.parse(rv);
                    form(post['id'],
                        function(html) {
                            $('#isso_' + post['id']).after(html);

                            var node = $("#issoform_" + post['id']);
                            $('textarea[id="comment"]', node).val(rv['text']);
                            $('input[id="author"]', node).val(rv['author']);
                            $('input[id="email"]', node).val(rv['email']);
                            $('input[id="website"]', node).val(rv['website']);
                            $('input[name="submit"]', node).val('Bestätigen.')
                        },
                        function(event) {
                            var node = $("#issoform_" + post['id']);
                            modify(post['id'], {
                                text: $('textarea[id="comment"]', node).val() || null,
                                author: $('input[id="author"]', node).val() || null,
                                email: $('input[id="email"]', node).val() || null,
                                website: $('input[id="website"]', node).val() || null,
                                parent: post['parent']
                            }, function(status, rv) {
                                update(JSON.parse(rv));
                                $('#issoform_' + post['id']).remove();
                            });
                        });
                    });
            } else {
                $('#issoform_' + post['id']).remove();
            };
            event.stop();
        });
    };

    // ability to answer directly to a comment
    $('footer > a:first-child', '#isso_' + post['id']).on('click', function(event) {

        if ($('#issoform_' + post['id']).length == 0) {
            form(post['id'],
                function(html) {
                    $('#isso_' + post['id']).after(html)
                },
                function(event) {
                    create({
                        text: $('textarea[id="comment"]').val() || null,
                        author: $('input[id="author"]').val() || null,
                        email: $('input[id="email"]').val() || null,
                        website: $('input[id="website"]').val() || null,
                        parent: post['id']
                    }, function(status, rv) {
                        $('#issoform_' + post['id']).remove();

                        if (status == 201) {
                            insert(JSON.parse(rv));
                        } // XXX else ...
                    });
                });
        } else {
            $('#issoform_' + post['id']).remove();
        };
        event.stop();
    });
};


/*
 * initialize form and fetch recent comments
 */

function initialize(thread) {

    // that with an unordered list
    thread.append('<ul id="comments"></ul>');

    // load our css
    $('head').append('<link rel="stylesheet" href="/static/style.css" />');

    // append form
    form(null, function(html) { thread.append(html) }, function(event) {
        create({
            text: $('textarea[id="comment"]').val() || null,
            author: $('input[id="author"]').val() || null,
            email: $('input[id="email"]').val() || null,
            website: $('input[id="website"]').val() || null,
            parent: null
        }, function(status, rv) {
            if (status == 201) {
                insert(JSON.parse(rv));
            }
        });
    });
};


function fetch(thread) {
    $.ajax('GET', '/1.0/' + encodeURIComponent(window.location.pathname) + '/',
    {}, {'Content-Type': 'application/json'}).then(function(status, rv) {

        if (status != 200) {
            return
        };

        rv = JSON.parse(rv);
        for (var item in rv) {
            insert(rv[item]);
        };
    });
}


$.domReady(function() {

    // initialize comment form and css
    initialize($('#isso_thread'));

    // fetch comments for path
    fetch($('#isso_thread'));

    // REMOVE ME
    $('input[id="author"]').val("Peter");
    $('textarea[id="comment"]').val("Lorem ipsum ...");

});
