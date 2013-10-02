/* Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 *
 * utility functions
 */

define(["app/markup"], function(Mark) {

    // return `cookie` string if set
    var cookie = function(cookie) {
        return (document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2];
    };

    var ago = function(date) {

        var diff = (((new Date()).getTime() - date.getTime()) / 1000),
            day_diff = Math.floor(diff / 86400);

        if (isNaN(day_diff) || day_diff < 0) {
            return;
        }

        var i18n = function(msgid, n) {
            if (! n) {
                return Mark.up("{{ i18n-" + msgid + " }}");
            } else {
                return Mark.up("{{ i18n-" + msgid + " | pluralize : `n` }}", {n: n});
            }
        };

        return day_diff === 0 && (
                diff <    60 && i18n("date-now")  ||
                diff <  3600 && i18n("date-minute", Math.floor(diff / 60)) ||
                diff < 86400 && i18n("date-hour", Math.floor(diff / 3600))) ||
            day_diff === 1 && i18n("date-day", day_diff) ||
            day_diff <  31 && i18n("date-week", Math.ceil(day_diff / 7)) ||
            day_diff < 365 && i18n("date-month", Math.ceil(day_diff / 30)) ||
            i18n("date-year", Math.ceil(day_diff / 365.25));
    };

    return {
        cookie: cookie,
        ago: ago
    };
});