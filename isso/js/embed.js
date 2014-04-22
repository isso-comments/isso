/*
 * Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * Distributed under the MIT license
 */

require(["app/lib/ready", "app/config", "app/api", "app/isso", "app/count", "app/dom", "app/markup", "app/text/css"], function(domready, config, api, isso, count, $, Mark, css) {

    "use strict";

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

        api.fetch($("#isso-thread").getAttribute("data-isso-id"), limit=20).then(
            function(rv) {
                if (rv.total_replies == 0) {
                    $("#isso-thread > h4").textContent = Mark.up("{{ i18n-no-comments }}");
                    return;
                }

                $("#isso-thread > h4").textContent = Mark.up("{{ i18n-num-comments | pluralize : `n` }}", {n: rv.total_replies});
                var lastcreated = 0;
                rv.replies.forEach(function(commentObject) {
                    isso.insert(commentObject, false);
                    if(commentObject.created > lastcreated) {
                        lastcreated = commentObject.created;
                    }
                });

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
