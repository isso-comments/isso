var default_config = require("app/default_config");
var utils = require("app/utils");

"use strict";

// Preserve default values to filter out when comparing
// with values fetched from server
var config = {};
for (var key in default_config) {
    config[key] = default_config[key];
}

var js = document.getElementsByTagName("script");

for (var i = 0; i < js.length; i++) {
    for (var j = 0; j < js[i].attributes.length; j++) {
        var attr = js[i].attributes[j];
        if (/^data-isso-/.test(attr.name)) {
            try {
                // Normalize underscores to dashes so that language-specific
                // strings can be caught better later on,
                // e.g. data-isso-postbox-text-text-PT_BR becomes
                // postbox-text-text-pt-br.
                // Also note that attr.name only gives lowercase strings as per
                // HTML spec, e.g. data-isso-FOO-Bar becomes foo-bar, but since
                // the test environment's jest-environment-jsdom seemingly does
                // not follow that convention, convert to lowercase here anyway.
                config[attr.name.substring(10)
                       .replace(/_/g, '-')
                       .toLowerCase()] = JSON.parse(attr.value);
            } catch (ex) {
                config[attr.name.substring(10)
                       .replace(/_/g, '-')
                       .toLowerCase()] = attr.value;
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

// Convert page-author-hash into a array by splitting at whitespace and/or commas
config["page-author-hashes"] = config["page-author-hashes"].split(/[\s,]+/);

module.exports = config;
