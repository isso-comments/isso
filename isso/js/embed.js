/*
 * Copyright 2014, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

var domready = require("app/lib/ready");
var config = require("app/config");
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

function init() {
    isso_thread = $('#isso-thread');
    heading = $.new("h4");

    if (config["css"] && $("style#isso-style") === null) {
        var style = $.new("link");
        style.id = "isso-style";
        style.rel ="stylesheet";
        style.type = "text/css";
        style.href = config["css-url"] ? config["css-url"] : api.endpoint + "/css/isso.css";
        $("head").append(style);
    }

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
    // Note: Not appending the isso.Postbox here since it relies
    // on the config object populated by elements fetched from the server,
    // and the call to fetch those is in fetchComments()
    isso_thread.append(heading);
    isso_thread.append('<div id="isso-root"></div>');
}

function fetchComments() {

    if (!$('#isso-root')) {
        return;
    }

    var isso_root = $('#isso-root');
    isso_root.textContent = '';
    api.fetch(isso_thread.getAttribute("data-isso-id") || location.pathname,
        config["max-comments-top"],
        config["max-comments-nested"]).then(
        function (rv) {
            for (var setting in rv.config) {
                if (setting in config && config[setting] != rv.config[setting]) {
                    console.log("Isso: Client value '%s' for setting '%s' overridden by server value '%s'.\n" +
                                "Since Isso version 0.12.6, 'data-isso-%s' is only configured via the server " +
                                "to keep client and server in sync",
                                config[setting], setting, rv.config[setting], setting);
                }
                config[setting] = rv.config[setting]
            }

            // Note: isso.Postbox relies on the config object populated by elements
            // fetched from the server, so it cannot be created in init()
            isso_root.prepend(new isso.Postbox(null));

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
                $(window.location.hash).scrollIntoView();
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
