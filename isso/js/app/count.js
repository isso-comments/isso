define(["app/api", "app/dom", "app/markup"], function(api, $, Mark) {
    return function() {
        $.each("a", function(el) {
            if (! el.href.match("#isso-thread$")) {
                return;
            }

            var tid = el.getAttribute("data-isso-id") ||
                      el.href.match("^(.+)#isso-thread$")[1]
                             .replace(/^.*\/\/[^\/]+/, '');

            api.count(tid).then(function(rv) {
                el.textContent = Mark.up("{{ i18n-num-comments | pluralize : `n` }}", {n: rv});
            });
        });
    };
});
