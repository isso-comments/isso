const utils = require("app/utils");

"use strict";

var config = {
    "css": true,
    "css-url": null,
    "lang": "",
    "default-lang": "en",
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

// create an array of normalized language codes from:
//   - config["lang"], if it is nonempty
//   - the first of navigator.languages, navigator.language, and
//     navigator.userLanguage that exists and has a nonempty value
//   - config["default-lang"]
//   - "en" as an ultimate fallback
// i18n.js will use the first code in this array for which we have
// a translation.
var languages = [];
var found_navlang = false;
if (config["lang"]) {
    languages.push(utils.normalize_bcp47(config["lang"]));
}
if (navigator.languages) {
    for (i = 0; i < navigator.languages.length; i++) {
        if (navigator.languages[i]) {
            found_navlang = true;
            languages.push(utils.normalize_bcp47(navigator.languages[i]));
        }
    }
}
if (!found_navlang && navigator.language) {
    found_navlang = true;
    languages.push(utils.normalize_bcp47(navigator.language));
}
if (!found_navlang && navigator.userLanguage) {
    found_navlang = true;
    languages.push(utils.normalize_bcp47(navigator.userLanguage));
}
if (config["default-lang"]) {
    languages.push(utils.normalize_bcp47(config["default-lang"]));
}
languages.push("en");

config["langs"] = languages;
// code outside this file should look only at langs
delete config["lang"];
delete config["default-lang"];

module.exports = config;
