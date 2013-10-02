require(["ready", "app/api", "app/isso", "app/count", "app/dom", "app/markup"], function(domready, api, isso, count, $, Mark) {

    "use strict";

    domready(function() {
        var css = $.new("link");
        css.type = "text/css";
        css.rel = "stylesheet";
        css.href = api.endpoint + "/css/isso.css";
        $("head").append(css);

        count();

        $("#isso-thread").append($.new('h4'));
        $("#isso-thread").append(new isso.Postbox(null));
        $("#isso-thread").append('<div id="isso-root"></div>');

        api.fetch().then(function(comments) {
            $("#isso-thread > h4").textContent = Mark.up("{{ i18n-num-comments | pluralize : `n` }}", {n: comments.length});
            for (var i=0; i < comments.length; i++) {
                isso.insert(comments[i], false);
            }
        }).fail(function() {
            $("#isso-thread > h4").textContent = Mark.up("{{ i18n-no-comments }}");
        });
    });
});