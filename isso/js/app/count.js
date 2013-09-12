define(["app/api", "lib/HTML"], function(api, HTML) {
    return function() {
        HTML.query("a").each(function(el, i, all) {
            if (! el.href.match("#isso-thread$")) {
                return;
            };

            var uri = el.href.match("^(.+)#isso-thread$")[1]
                .replace(/^.*\/\/[^\/]+/, '');
            console.log(uri)
            api.count(uri).then(function(rv) {
                el.textContent = rv + (rv > 1 ? " Kommentare" : " Kommentar");
            })
        });
    }
});