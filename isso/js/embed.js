require(["ready", "app/api", "app/isso", "app/count", "app/dom", "app/markup"], function(domready, api, isso, count, $, Mark) {

    "use strict";

    domready(function() {
        var css = $.new("link");
        css.type = "text/css";
        css.rel = "stylesheet";
        css.href = api.endpoint + "/css/isso.css";
        $("head").append(css);

        count();

        if ($("#isso-thread") === null) {
            return console.log("abort, #isso-thread is missing");
        }

        $("#isso-thread").append($.new('h4'));
        $("#isso-thread").append(new isso.Postbox(null));
        $("#isso-thread").append('<div id="isso-root"></div>');

        api.fetch().then(function(rv) {

            if (! rv.length) {
                $("#isso-thread > h4").textContent = Mark.up("{{ i18n-no-comments }}");
                return;
            }

            $("#isso-thread > h4").textContent = Mark.up("{{ i18n-num-comments | pluralize : `n` }}", {n: rv.length});
            for (var i=0; i < rv.length; i++) {
                isso.insert(rv[i], false);
            }
        }).fail(function(err) {
            console.log(err);
        }).done(function() {
            if (window.location.hash.length > 0) {
                $(window.location.hash).scrollIntoView();
            }
        });
    });
});
