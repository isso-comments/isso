require(["lib/ready", "app/count"], function(domready, count) {
    domready(function() {
        count();
    })
});
