"use strict";

var default_config = {
    "css": true,
    "css-url": null,
    "lang": null,
    "default-lang": "en",
    "reply-to-self": false,
    "require-email": false,
    "require-author": false,
    "reply-notifications": false,
    "reply-notifications-default-enabled": false,
    "max-comments-top": "inf",
    "max-comments-nested": 5,
    "reveal-on-click": 5,
    "sorting": "oldest",
    "gravatar": false,
    "avatar": true,
    "avatar-bg": "#f0f0f0",
    "avatar-fg": ["#9abf88", "#5698c4", "#e279a3", "#9163b6",
                  "#be5168", "#f19670", "#e4bf80", "#447c69"].join(" "),
    "vote": true,
    "vote-levels": null,
    "feed": false,
    "page-author-hashes": "",
};
Object.freeze(default_config);

module.exports = default_config;
