define(["app/markup"], function(Mark) {

    // return `cookie` string if set
    var cookie = function(cookie) {
        return (document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2];
    };

    var ago = function(localTime, date) {

        var secs = ((localTime.getTime() - date.getTime()) / 1000)

        if (isNaN(secs) || secs < 0 ) {
            secs = 0;
        }

        var mins = Math.ceil(secs / 60), hours = Math.ceil(mins / 60),
            days = Math.ceil(hours / 24);

        var i18n = function(msgid, n) {
            if (! n) {
                return Mark.up("{{ i18n-" + msgid + " }}");
            } else {
                return Mark.up("{{ i18n-" + msgid + " | pluralize : `n` }}", {n: n});
            }
        };

        return secs  <=  45 && i18n("date-now")  ||
               secs  <=  90 && i18n("date-minute", 1) ||
               mins  <=  45 && i18n("date-minute", mins) ||
               mins  <=  90 && i18n("date-hour", 1) ||
               hours <=  22 && i18n("date-hour", hours) ||
               hours <=  36 && i18n("date-day", 1) ||
               days  <=   5 && i18n("date-day", days) ||
               days  <=   8 && i18n("date-week", 1) ||
               days  <=  21 && i18n("date-week", Math.ceil(days / 7)) ||
               days  <=  45 && i18n("date-month", 1) ||
               days  <= 345 && i18n("date-month", Math.ceil(days / 30)) ||
               days  <= 547 && i18n("date-year", 1) ||
                               i18n("date-year", Math.ceil(days / 365.25));
    };

    return {
        cookie: cookie,
        ago: ago
    };
});
