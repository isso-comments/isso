/*
 * Copyright 2014, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

require(["app/lib/ready", "app/config", "app/i18n", "app/api", "app/isso", "app/count", "app/dom", "app/text/css", "app/text/svg", "app/jade", "app/social/openid", "app/social/facebook", "app/social/google"], function(domready, config, i18n, api, isso, count, $, css, svg, jade, openid, facebook, google) {

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

        $("#isso-thread").append($.new('h4'));
        $("#isso-thread").append(new isso.Postbox(null));
        $("#isso-thread").append('<div id="isso-root"></div>');

        openid.init();
        facebook.init();
        google.init();

        api.fetch($("#isso-thread").getAttribute("data-isso-id"),
            config["max-comments-top"],
            config["max-comments-nested"]).then(
            function(rv) {
                if (rv.total_replies === 0) {
                    $("#isso-thread > h4").textContent = i18n.translate("no-comments");
                    return;
                }

                var lastcreated = 0;
                var count = rv.total_replies;
                rv.replies.forEach(function(comment) {
                    isso.insert(comment, false);
                    if(comment.created > lastcreated) {
                        lastcreated = comment.created;
                    }
                    count = count + comment.total_replies;
                });
                $("#isso-thread > h4").textContent = i18n.pluralize("num-comments", count);

                if(rv.hidden_replies > 0) {
                    isso.insert_loader(rv, lastcreated);
                }

                if (window.location.hash.length > 0) {
                    $(window.location.hash).scrollIntoView();
                }
            },
            function(err) {
                console.log(err);
            }
        );
    });
});
