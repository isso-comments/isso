/*
 * Copyright 2014, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

var domready = require("app/lib/ready");
var config = require("app/config");
var default_config = require("app/default_config");
var i18n = require("app/i18n");
var api = require("app/api");
var isso = require("app/isso");
var count = require("app/count");
var $ = require("app/dom");
var svg = require("app/svg");
var template = require("app/template");

"use strict";

template.set("conf", config);
template.set("i18n", i18n.translate);
template.set("pluralize", i18n.pluralize);
template.set("svg", svg);

var isso_thread;
var heading;
var postbox;

function init() {
    // Fetch config from server, will override any local data-isso-* attributes
    api.config().then(
        function (rv) {
            for (var setting in rv.config) {
                if (setting in config
                    && config[setting] != default_config[setting]
                    && config[setting] != rv.config[setting]) {
                    console.log("Isso: Client value '%s' for setting '%s' overridden by server value '%s'.\n" +
                                "Since Isso version 0.12.6, 'data-isso-%s' is only configured via the server " +
                                "to keep client and server in sync",
                                config[setting], setting, rv.config[setting], setting);
                }
                config[setting] = rv.config[setting]
            }
        },
        function(err) {
            console.log(err);
        }
    );

    if (config["css"] && $("style#isso-style") === null) {
        var style = $.new("link");
        style.id = "isso-style";
        style.rel ="stylesheet";
        style.type = "text/css";
        style.href = config["css-url"] ? config["css-url"] : api.endpoint + "/css/isso.css";
        $("head").append(style);
    }

    isso_thread = $('#isso-thread');
    heading = $.new('h4.isso-thread-heading');
    postbox = new isso.Postbox(null);

    count();

    if (isso_thread === null) {
        return console.log("abort, #isso-thread is missing");
    }

    if (config["feed"]) {
        var feedLink = $.new('a', i18n.translate('atom-feed'));
        var feedLinkWrapper = $.new('span.isso-feedlink');
        feedLink.href = api.feed(isso_thread.getAttribute("data-isso-id"));
        feedLinkWrapper.appendChild(feedLink);
        isso_thread.append(feedLinkWrapper);
    }

    // Only insert elements if not already present, respecting Single-Page-Apps
    if (!$('h4.isso-thread-heading')) {
        isso_thread.append(heading);
    }
    if (!$('.isso-postbox')) {
        isso_thread.append(postbox);
    } else {
        $('.isso-postbox').value = postbox;
    }
    if (!$('#isso-root')) {
        isso_thread.append('<div id="isso-root"></div>');
    }

    window.addEventListener('hashchange', function() {
        if (!window.location.hash.match("^#isso-[0-9]+$")) {
            return;
        }

        var existingTarget = $(".isso-target");
        if (existingTarget != null) {
            existingTarget.classList.remove("isso-target");
        }

        try {
            $(window.location.hash + " > .isso-text-wrapper").classList.add("isso-target");
        } catch(ex) {
            // selector probably doesn't exist as element on page
        }
    });
}

function fetchComments() {

    var isso_root = $('#isso-root');
    if (!isso_root) {
        return;
    }
    isso_root.textContent = '';

    api.fetch(isso_thread.getAttribute("data-isso-id") || location.pathname,
        config["max-comments-top"],
        config["max-comments-nested"]).then(
        function (rv) {

            if (rv.total_replies === 0) {
                heading.textContent = i18n.translate("no-comments");
                return;
            }

            var lastcreated = 0;
            var count = rv.total_replies;
            rv.replies.forEach(function(comment) {
                isso.insert(comment, false);
                if (comment.created > lastcreated) {
                    lastcreated = comment.created;
                }
                count = count + comment.total_replies;
            });
            heading.textContent = i18n.pluralize("num-comments", count);

            if (rv.hidden_replies > 0) {
                isso.insert_loader(rv, lastcreated);
            }

            if (window.location.hash.length > 0 &&
                window.location.hash.match("^#isso-[0-9]+$")) {
                try {
                    $(window.location.hash).scrollIntoView();

                    // We can't just set the id to `#isso-target` because it's already set to `#isso-[number]`
                    // So a class `.isso-target` has to be used instead, and then we can manually remove the
                    // class from the old target comment in the `hashchange` listener.
                    $(window.location.hash + " > .isso-text-wrapper").classList.add("isso-target");
                } catch(ex) {
                    // selector probably doesn't exist as element on page
                }
            }
        },
        function(err) {
            console.log(err);
        }
    );
}

domready(function() {
    init();
    fetchComments();
});

window.Isso = {
    init: init,
    fetchComments: fetchComments
};
