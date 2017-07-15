define(function() {
    "use strict";

    var init = function(server_conf) {

        for (var setting in server_conf) {
            this[setting] = server_conf[setting];
        }

        if (this["lang"] == "auto") {
            this["lang"] = (navigator.language || navigator.userLanguage).split("-")[0];
        }

        // Hash tag must be 'escaped' with a backslash in config file,
        // but the backslash is not removed by ConfigParser. Also
        // split avatar-fg into a list on white space.
        this["avatar-fg"] = this["avatar-fg"].replace(/\\#/g, "#").split(" ");
        this["avatar-bg"] = this["avatar-bg"].replace(/\\#/g, "#")

    };

    return {
        init: init
    };
});
