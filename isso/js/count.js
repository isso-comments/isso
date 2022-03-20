const domready = require("app/lib/ready");
const count = require("app/count");

domready(function() {
    count();
});
