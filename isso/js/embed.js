/*
 * Copyright 2014, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

require(["app/lib/ready", "app/config", "app/i18n", "app/api", "app/isso", "app/count", "app/dom", "app/text/css", "app/text/svg", "app/jade", "app/lib/promise"], function(domready, config, i18n, api, isso, count, $, css, svg, jade, Q) {

    "use strict";

    jade.set("conf", config);
    jade.set("i18n", i18n.translate);
    jade.set("pluralize", i18n.pluralize);
    jade.set("svg", svg);

    domready(function() {

        if (config["css"]) {
            var style = $.new("style");
            style.type = "text/css";
            style.textContent = css.inline;
            $("head").append(style);
        }

        count();

        if ($("#isso-thread") === null) {
            return console.log("abort, #isso-thread is missing");
        }

        var server = null,
            comments = null;

        api.info().then(
            function (rv) {
                server = rv;

                $("#isso-thread").append($.new('h4'));
                $("#isso-thread").append(new isso.Postbox(server, null));
                $("#isso-thread").append('<div id="isso-root"></div>');

                tryInitComments();
            },
            errorHandler
        );

        api.fetch(
            $("#isso-thread").getAttribute("data-isso-id"),
            config["max-comments-top"],
            config["max-comments-nested"]).then(
            function (rv) {
                comments = rv;
                tryInitComments();
            },
            errorHandler
        );

        function tryInitComments() {
            if (!server || !comments) {
                return;
            }

            if (comments.total_replies === 0) {
                $("#isso-thread > h4").textContent = i18n.translate("no-comments");
                return;
            }

            var lastcreated = 0;
            var count = comments.total_replies;
            comments.replies.forEach(function(comment) {
                isso.insert(comment, server, false);
                if(comment.created > lastcreated) {
                    lastcreated = comment.created;
                }
                count = count + comment.total_replies;
            });
            $("#isso-thread > h4").textContent = i18n.pluralize("num-comments", count);

            if(comments.hidden_replies > 0) {
                isso.insert_loader(comments, server, lastcreated);
            }

            if (window.location.hash.length > 0) {
                $(window.location.hash).scrollIntoView();
            }
        }

        function errorHandler(err) {
            console.log(err);
        }
    });
});
