/* Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 */


var isso = isso || {};


function initialize() {

    $('div.buttons > a').forEach(function(item) {

        var node = $(item).parent().parent().parent().parent()[0],
            id = node.getAttribute("data-id");
        isso.path = node.getAttribute("data-path");

        if (item.text == 'Approve') {
            $(item).on('click', function(event) {
                isso.approve(id, function(status, rv) {
                    $(node).prependTo($('#approved'));
                    $('.approve', node).remove();
                });
                event.stop();
            });
        } else {
            $(item).on('click', function(event) {
                if (confirm("RLY?") == true) {
                    isso.remove(id, function(status, rv) {
                        $(node).remove()
                    });
                };
                event.stop();
            });
        };
    });
};


$.domReady(function() {
    initialize();
});
