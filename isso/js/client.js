/* Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 */

 var isso = isso || {};


function form(id, defaults, func) {
    /*
    Returns HTML for form and registers submit call.

    Synopsis: `isso_N` is the comment with the id N. `issoform` is a new
    form to write an answer to the article or answer to a comment using
    `issoform_N` where N is the id to respond to.

    :param id: comment id
    :param returnfunc: function, that takes one argument (the HTML to display the form)
    :param func: function, when the user submits the form
    */

    var rv = $(brew([
        'div', {'class': 'issoform', 'id': 'issoform' + (id ? ('_' + id) : '')},
            ['div',
                ['input', {'type': 'text', 'name': 'author', 'id': 'author', 'value': defaults.author || "", 'placeholder': "Name"}]],
            ['div',
                ['input', {'type': 'email', 'name': 'email', 'id': 'email', 'value': defaults.email || "", 'placeholder': "Email"}]],
            ['div',
                ['input', {'type': 'url', 'name': 'website', 'id': 'website', 'value': defaults.website || "", 'placeholder': "Website"}]],
            ['div',
                ['textarea', defaults.text || "", {'rows': '10', 'name': 'text', 'id': 'comment', 'placeholder': "Comment"}]],
            ['div',
                ['input', {'type': 'submit', 'value': 'Add Comment'}]],
    ]));

    $('input[type="submit"]', rv).on('click', function(event) {
        func(rv, id);
        event.stop();
    });
    return rv;
}


function extract(form, parent) {
    return {
        text: $('textarea[id="comment"]', form).val() || null,
        author: $('input[id="author"]', form).val() || null,
        email: $('input[id="email"]', form).val() || null,
        website: $('input[id="website"]', form).val() || null,
        parent: parent
    };
}


function edit() {

}


function commit(form, parent) {
    isso.create(extract(form, parent), function(status, rv) {
        if (status == 201 || status == 202) {
            insert(JSON.parse(rv));
        }
    });
}


var insert = function insert(post) {
    /*
    Insert a comment into #isso_thread.

    :param post: JSON from API call
    */

    var path = encodeURIComponent(window.location.pathname),
        date = new Date(parseInt(post['created']) * 1000);

    // create <ul /> for parent, if used
    if (post['parent'])
        $('#isso_' + post['parent']).append('<ul></ul>');

    $(post['parent'] ? '#isso_' + post['parent'] + ' > ul:last-child' : '#isso_thread > ul')
    .append(brew([
        'article', {'class': 'isso', 'id': 'isso_' + post['id']},
            ['header'], ['div'], ['footer']
    ]));

    var node = $('#isso_' + post['id']),
        author = post['author'] || 'Anonymous';

    if (post['website'])
        author = brew(['a', {'href': post['website'], 'rel': 'nofollow'}]);

    // deleted
    if (post['mode'] == 4) {
        node.addClass('deleted');
        $('header', node).append('Kommentar entfernt')
        $('div', node).append('<p>&nbsp;</p>')
        return;
    }

    $('header', node).append('<span class="author">' + author + '</span>');
    if (post['mode'] == 2 )
        $('header', node).append(brew(['span', {'class': 'note'}, 'Kommentar muss noch freigeschaltet werden']));

    $('div', node).html(post['text']);

    $('footer', node).append(brew([
        'a', {'href': '#'}, 'Antworten',
    ])).append(brew([
        'a', {'href': '#isso_' + post['id']}, '#' + post['id'],
    ])).append(brew([
        'time', {'datetime': date.getUTCFullYear() + '-' + date.getUTCMonth() + '-' + date.getUTCDate()}, format(date)
    ]));

    if (read(path + '-' + post['id'])) {
        $('#isso_' + post['id'] + '> footer > a:first-child')
            .after(brew(['a', {'class': 'delete', 'href': '#'}, 'Löschen']))
            .after(brew(['a', {'class': 'edit', 'href': '#'}, 'Bearbeiten']));

        // DELETE
        $('#isso_' + post['id'] + ' > footer .delete').on('click', function(event) {
            isso.remove(post['id'], function(status, rv) {
                // XXX comment might not actually deleted
                $('#isso_' + post['id']).remove();
            });
            event.stop();
        });

        // EDIT
        $('#isso_' + post['id'] + ' > footer .edit').on('click', function(event) {

            if ($('#issoform_' + post['id']).length == 0) {  // HTML form not shown
                isso.plain(post['id'], function(status, rv) {
                    if (status != 200) return alert('Mööp');
                    var rv = form(post['id'], JSON.parse(rv), function(form, id) {
                        isso.modify(id, extract(form, post['parent']), function(status, rv) {
                            if (status != 200) return alert('Mööp');

                            $('#issoform_' + post['id']).remove();
                            $('#isso_' + post['id']).remove();
                            insert(JSON.parse(rv));
                        });
                    });

                    $('#isso_' + post['id']).after(rv);
                    $('input[type="submit"]', rv)[0].value = 'Bestätigen.';
                });
            } else {
                $('#issoform_' + post['id']).remove();
            }
            event.stop();
        });
    }

    // ability to answer directly to a comment
    $('footer > a:first-child', '#isso_' + post['id']).on('click', function(event) {

        if ($('#issoform_' + post['id']).length == 0) {  // HTML form not shown
            $('#isso_' + post['id']).after(form(post['id'], {}, function(form, id) {
                commit(form, id);
                // XXX: animation (aka user feedback)
                $('#issoform_' + post['id']).remove();
            }));
        } else {
            $('#issoform_' + post['id']).remove();
        }
        event.stop();
    });
}


/*
 * initialize form and fetch recent comments
 */

function initialize(thread) {
    var html;

    thread.append('<ul id="comments"></ul>');
    $('head').append('<link rel="stylesheet" href="/static/style.css" />');

    html = form(null, {}, commit);
    thread.append(html);
}


function fetch(thread) {
    $.ajax('GET', isso.prefix + '/1.0/' + encodeURIComponent(window.location.pathname),
    {}, {'Content-Type': 'application/json'}).then(function(status, rv) {

        if (status != 200) {
            return
        }

        rv = JSON.parse(rv);
        for (var item in rv) {
            insert(rv[item]);
        }
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
