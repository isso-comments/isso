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


function zfill(arg, i) {
    var res = String(arg);
    if (res.length < i) {
        for (var j = 0; j <= (i - res.length); j++) {
            res = '0' + res;
        };
    };

    return res;
};


/*
 * isso specific helpers to create, modify, delete and receive comments
 */

function isso(method, path, data, success, error) {
    $.ajax({
        url: path,
        method: method,
        type: 'json',
        headers: {
            'Content-Type': 'application/json'
        },
        data: JSON.stringify(data),
        error: function(rv) {
            error(rv) || alert("Mööp.");
        },
        success: function(rv) {
            success(rv);
        }
    });
};


function verify(data) {
    return data['text'] == null ? false : true
};


function create(data, success) {

    if (!verify(data)) {
        return;
    }

    isso('POST', '/1.0/' + encodeURIComponent(window.location.pathname) + '/new', data, success);
};


function modify(id, data, success) {
    if (!verify(data)) {
        return;
    }

    isso('PUT', '/1.0/' + encodeURIComponent(window.location.pathname) + '/' + id, data, success);
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


function insert(thread, post) {
    /*
    Insert a comment into #isso_thread.

    :param thread: XXX remove this
    :param post: JSON from API call
    */

    // pythonic strftime
    var format = function(date, lang, fmt) {

        var months = {'de': [
            'Januar', 'Februar', 'März', 'April', 'Mai', 'Juni', 'Juli',
            'August', 'September', 'Oktober', 'November', 'Dezember'],
                      'en': [
            'January', 'February', 'March', 'April', 'May', 'June', 'July',
            'August', 'September', 'October', 'November', 'December'],
        };

        var conversions = [
            ['%Y', date.getFullYear()], ['%m', zfill(date.getMonth(), 2)],
            ['%B', months[lang][date.getMonth() - 1]],
            ['%d', zfill(date.getDate(), 2)], ['%H', zfill(date.getHours(), 2)],
            ['%H', zfill(date.getHours(), 2)], ['%M', zfill(date.getMinutes(), 2)],
        ];

        conversions.map(function(item) { fmt = fmt.replace(item[0], item[1]) });
        return fmt;
    };

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
        '  </header>' + post['text'] +
        '  <footer>' +
        '    <a href="#">Antworten</a>' +
        '    <a href="#isso_' + post['id'] + '">#' + post['id'] + '</a>' +
        '    <span class="date">' + format(date, 'de', '%d.%m.%Y um %H:%M') +
        '    </span>' +
        '  </footer>' +
        '</article>');

    if (read('session-' + encodeURIComponent(window.location.pathname) + '-' + post['id'])) {
        $('#isso_' + post['id'] + '> footer > a:first-child')
            .after('<a class="delete" href="#">Löschen</a>')
            .after('<a class="edit" href="#">Bearbeiten</a>');

        // DELETE
        $('#isso_' + post['id'] + ' > footer .delete').on('click', function(event) {
            $.ajax({
                url: '/1.0/' + encodeURIComponent(window.location.pathname) + '/' + post['id'],
                method: 'DELETE',
                error: function(resp) {
                    alert('Mööp!');
                },
                success: function(res) {
                    // XXX comment might not actually deleted
                    $('#isso_' + post['id']).remove();
                },
            });
            event.stop();
        });

        // EDIT
        $('#isso_' + post['id'] + ' > footer .edit').on('click', function(event) {
            $.ajax({
                url: '/1.0/' + encodeURIComponent(window.location.pathname) + '/' + post['id'],
                method: 'PUT',
                error: function(resp) {
                    alert('Mööp!');
                },
                success: function(res) {
                    // XXX comment might not actually deleted
                    $('#isso_' + post['id']).remove();
                },
            });
            event.stop();
        });
    }

    // ability to answer directly to a comment
    $('footer > a:first-child', '#isso_' + post['id']).on('click', function(event) {

        if ($('#issoform_' + post['id']).length == 0) {
            form(post['id'], function(html) {$('#isso_' + post['id']).after(html)});
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
        }, function(rv) {
            insert($('#isso_thread'), rv);
        });
    });
};


function fetch(thread) {
    var rv = $.ajax({
        url: '/1.0/' + encodeURIComponent(window.location.pathname) + '/',
        method: 'GET',
        type: 'json',
        headers: {
            'Content-Type': 'application/json',
        },
        error: function(resp) {
            return;
        },
        success: function(resp) {
            for (var item in resp) {
                insert(thread, resp[item]);
            }
        }
    });
};

$.domReady(function() {

    // initialize comment form and css
    initialize($('#isso_thread'));

    // fetch comments for path
    fetch($('#isso_thread'));

    // REMOVE ME
    $('input[id="author"]').val("Peter");
    $('textarea[id="comment"]').val("Lorem ipsum ...");

});
