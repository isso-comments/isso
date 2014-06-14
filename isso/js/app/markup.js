define(["vendor/markup", "app/config", "app/i18n", "app/text/svg"], function(Mark, config, i18n, svg) {

    "use strict";


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
        conf: config,
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