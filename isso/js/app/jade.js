define(["libjs-jade-runtime", "app/utils", "jade!app/text/postbox", "jade!app/text/comment", "jade!app/text/comment-loader"], function(runtime, utils, tt_postbox, tt_comment, tt_comment_loader) {
    "use strict";

    var globals = {},
        templates = {};

    var load = function(name, js) {
        templates[name] = (function(jade) {
                var fn;
                eval("fn = " + js);
                return fn;
            })(runtime);
    };

    var set = function(name, value) {
            globals[name] = value;
    };

    load("postbox", tt_postbox);
    load("comment", tt_comment);
    load("comment-loader", tt_comment_loader);

    set("bool", function(arg) { return arg ? true : false; });
    set("datetime", function(date) {
        if (typeof date !== "object") {
            date = new Date(parseInt(date, 10) * 1000);
        }

        return Array.join([
            date.getUTCFullYear(),
            utils.pad(date.getUTCMonth(), 2),
            utils.pad(date.getUTCDay(), 2)], "-");
    });

    return {
        "set": set,
        "render": function(name, locals) {
            var rv, t = templates[name];
            if (! t) {
                throw "Template not found: '" + name + "'";
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
        }
    };
});