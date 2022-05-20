var utils = require("app/utils");

var tmpl_postbox = require("app/templates/postbox");
var tmpl_comment = require("app/templates/comment");
var tmpl_comment_loader = require("app/templates/comment-loader");

"use strict";

var globals = {},
    templates = {};

var load_tmpl = function(name, tmpl) {
    templates[name] = tmpl;
};

var set = function(name, value) {
    globals[name] = value;
};

load_tmpl("postbox", tmpl_postbox);
load_tmpl("comment", tmpl_comment);
load_tmpl("comment-loader", tmpl_comment_loader);

set("humanize", function(date) {
    if (typeof date !== "object") {
        date = new Date(parseInt(date, 10) * 1000);
    }

    return date.toString();
});
set("datetime", function(date) {
    if (typeof date !== "object") {
        date = new Date(parseInt(date, 10) * 1000);
    }

    return [
        date.getUTCFullYear(),
        // getUTCMonth returns zero-based month!
        utils.pad(date.getUTCMonth() + 1, 2),
        // getUTCDay returns day of week, not month!
        utils.pad(date.getUTCDate(), 2)
    ].join("-") + "T" + [
        utils.pad(date.getUTCHours(), 2),
        utils.pad(date.getUTCMinutes(), 2),
        utils.pad(date.getUTCSeconds(), 2)
    ].join(":") + "Z";
});

var render = function(name, locals) {
    var rv, t = templates[name];
    if (! t) {
        throw new Error("Template not found: '" + name + "'");
    }

    locals = locals || {};

    var keys = [];
    for (var key in locals) {
        if (locals.hasOwnProperty(key) && !globals.hasOwnProperty(key)) {
            keys.push(key);
            globals[key] = locals[key];
        }
    }

    rv = templates[name](globals);

    for (var i = 0; i < keys.length; i++) {
        delete globals[keys[i]];
    }

    return rv;
};

module.exports = {
    set: set,
    render: render,
};
