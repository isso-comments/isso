require(["app/lib/ready", "app/count"], function(domready, count) {
    domready(function() {
        count();
    });
});
