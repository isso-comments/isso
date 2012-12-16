
function initialize() {

    $('div.buttons > a').forEach(function(item) {

        var node = $(item).parent().parent().parent().parent()[0]
        var path = node.getAttribute("data-path");
        var id = node.getAttribute("data-id");

        if (item.text == 'Approve') {
            $(item).on('click', function(event) {
                $.ajax('PUT', '/1.0/' + encodeURIComponent(path) + '/' + id + '/approve')
                 .then(function(status, rv) {
                    $(node).prependTo($('#approved'));
                    $('.approve', node).remove();
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
