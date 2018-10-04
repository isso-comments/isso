define(function() {
    "use strict";

    var config = {
        "css": true,
        "lang": (navigator.language || navigator.userLanguage).split("-")[0],
        "reply-to-self": false,
        "require-email": false,
        "require-author": false,
        "reply-notifications": false,
        "max-comments-top": "inf",
        "max-comments-nested": 5,
        "reveal-on-click": 5,
        "gravatar": false,
        "avatar": true,
        "avatar-bg": "#f0f0f0",
        "avatar-fg": ["#9abf88", "#5698c4", "#e279a3", "#9163b6",
                      "#be5168", "#f19670", "#e4bf80", "#447c69"].join(" "),
        "vote": true,
        "vote-levels": null,
        "feed": false
    };

    var js = document.getElementsByTagName("script");

    for (var i = 0; i < js.length; i++) {
        for (var j = 0; j < js[i].attributes.length; j++) {
            var attr = js[i].attributes[j];
            if (/^data-isso-/.test(attr.name)) {
                try {
                    config[attr.name.substring(10)] = JSON.parse(attr.value);
                } catch (ex) {
                    config[attr.name.substring(10)] = attr.value;
                }
            }
        }
    }

    // split avatar-fg on whitespace
    config["avatar-fg"] = config["avatar-fg"].split(" ");

    return config;

});
