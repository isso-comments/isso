
function initialize() {

    $('article > footer > a').forEach(function(item) {

        var node = $(item).parent().parent()[0]
        var path = node.getAttribute("data-path");
        var id = node.getAttribute("data-id");

        if (item.text == 'Approve') {
            $(item).on('click', function(event) {
                $.ajax('PUT', '/1.0/' + encodeURIComponent(path) + '/' + id + '/approve')
                 .then(function(status, rv) {
                    // $(node).detach();
                    $('h2.recent + span').after(node);
                 });
                event.stop();
            });
        } else {
            $(item).on('click', function(event) {
                if (confirm("RLY?") == true) {
                    $.ajax('DELETE', '/1.0/' + encodeURIComponent(path) + '/' + id)
                     .then(function() {
                        $(node).remove()
                    });
               };
                event.stop();
            });
        };
    });
};


$.domReady(function() {
    initialize();
});
