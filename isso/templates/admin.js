
function remove(path, id, func) {
    $.ajax({
        url: '/1.0/' + encodeURIComponent(path) + '/' + id,
        method: 'DELETE',
        type: 'json',
        error: function(resp) {
            alert('Mööp.');
        },
        success: function(resp) {
            func();
        },
    });
};


// function approve(path, id, func) {
//     $.ajax({
//         url: ''
//     })
// }


function initialize() {

    $('article > footer > a').forEach(function(item) {

        var node = $(item).parent().parent()[0]
        var path = node.getAttribute("data-path");
        var id = node.getAttribute("data-id");

        if (item.text == 'Approve') {
            $(item).on('click', function(event) {
                event.stop();
            });
        } else {
            $(item).on('click', function(event) {
               if (confirm("RLY?") == true) {
                    remove(path, id, function() {
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
