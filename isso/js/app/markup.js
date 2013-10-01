define(["lib/markup", "./i18n", "text/svg"], function(Mark, i18n, svg) {

    "use strict";

    var pad = function(n, width, z) {
        z = z || '0';
        n = n + '';
        return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
    };

    // circumvent https://github.com/adammark/Markup.js/issues/22
    function merge(obj) {
        var result = {};
        for (var prefix in obj) {
            for (var attrname in obj[prefix]) {
                result[prefix + "-" + attrname] = obj[prefix][attrname];
            }
        }
        return result;
    }

    Mark.delimiter = ":";
    Mark.includes = merge({
        i18n: i18n[i18n.lang],
        svg: svg
    });

    Mark.pipes.datetime = function(date) {
        if (typeof date !== "object") {
            date = new Date(parseInt(date, 10) * 1000);
        }

        return [date.getUTCFullYear(), pad(date.getUTCMonth(), 2), pad(date.getUTCDay(), 2)].join("-");
    };

    Mark.pipes.substract = function(a, b) {
        return parseInt(a, 10) - parseInt(b, 10);
    };

    Mark.pipes.pluralize = function(str, n) {
        return i18n.plurals[i18n.lang](str.split("\n"), +n).trim();
    };

    var strip = function(string) {
        // allow whitespace between Markup.js delimiters such as
        // {{ var | pipe : arg }} instead of {{var|pipe:arg}}
        return string.replace(/\{\{\s*(.+?)\s*\}\}/g, function(match, val) {
            return ("{{" + val + "}}").replace(/\s*\|\s*/g, "|")
                                      .replace(/\s*\:\s*/g, ":");
        });
    };

    return {
        up: function(template, context) {
            return Mark.up(strip(template), context);
        }
    };
});