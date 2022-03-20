/*
 * Copyright 2014, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

const domready = require("app/lib/ready");
const config = require("app/config");
const i18n = require("app/i18n");
const api = require("app/api");
const isso = require("app/isso");
const count = require("app/count");
const $ = require("app/dom");
const svg = require("app/svg");
const template = require("app/template");

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

    $('#isso-root').textContent = '';
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

            // Finally, create Postbox with configs fetched from server
            isso_thread.append(new isso.Postbox(null));

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
