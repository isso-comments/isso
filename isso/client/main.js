require(["minified"], function(minified) {
    console.log(minified)
    minified.$.ready(function() {
        console.log(123);
    })
});
