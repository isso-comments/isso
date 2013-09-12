require(["lib/ready", "app/isso", "app/count"], function(domready, isso, count) {
    domready(function() {
        count();
        isso.init();
    })
});
