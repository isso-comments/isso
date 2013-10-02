require(["ready", "app/count"], function(domready, count) {
    domready(function() {
        count();
    })
});
