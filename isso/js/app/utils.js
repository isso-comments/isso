define(["app/i18n"], function(i18n) {
    "use strict";

    // return `cookie` string if set
    var cookie = function(cookie) {
        return (document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2];
    };

    var pad = function(n, width, z) {
        z = z || '0';
        n = n + '';
        return n.length >= width ? n : new Array(width - n.length + 1).join(z) + n;
    };

    var ago = function(localTime, date) {

        var secs = ((localTime.getTime() - date.getTime()) / 1000);

        if (isNaN(secs) || secs < 0 ) {
            secs = 0;
        }

        var mins = Math.floor(secs / 60), hours = Math.floor(mins / 60),
            days = Math.floor(hours / 24);

        return secs  <=  45 && i18n.translate("date-now")  ||
               secs  <=  90 && i18n.pluralize("date-minute", 1) ||
               mins  <=  45 && i18n.pluralize("date-minute", mins) ||
               mins  <=  90 && i18n.pluralize("date-hour", 1) ||
               hours <=  22 && i18n.pluralize("date-hour", hours) ||
               hours <=  36 && i18n.pluralize("date-day", 1) ||
               days  <=   5 && i18n.pluralize("date-day", days) ||
               days  <=   8 && i18n.pluralize("date-week", 1) ||
               days  <=  21 && i18n.pluralize("date-week", Math.floor(days / 7)) ||
               days  <=  45 && i18n.pluralize("date-month", 1) ||
               days  <= 345 && i18n.pluralize("date-month", Math.floor(days / 30)) ||
               days  <= 547 && i18n.pluralize("date-year", 1) ||
                               i18n.pluralize("date-year", Math.floor(days / 365.25));
    };

    var HTMLEntity = {
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': '&quot;',
        "'": '&#39;',
        "/": '&#x2F;'
    };

    var escape = function(html) {
        return String(html).replace(/[&<>"'\/]/g, function (s) {
            return HTMLEntity[s];
        });
    };

    var text = function(html) {
        var _ = document.createElement("div");
        _.innerHTML = html.replace(/<div><br><\/div>/gi, '<br>')
                          .replace(/<div>/gi,'<br>')
                          .replace(/<br>/gi, '\n')
                          .replace(/&nbsp;/gi, ' ');
        return _.textContent.trim();
    };

    var detext = function(text) {
        text = escape(text);
        return text.replace(/\n\n/gi, '<br><div><br></div>')
                   .replace(/\n/gi, '<br>');
    };

    // Safari private browsing mode supports localStorage, but throws QUOTA_EXCEEDED_ERR
    var localStorageImpl;
    try {
        localStorage.setItem("x", "y");
        localStorage.removeItem("x");
        localStorageImpl = localStorage;
    } catch (ex) {
        localStorageImpl = (function(storage) {
            return {
                setItem: function(key, val) {
                    storage[key] = val;
                },
                getItem: function(key) {
                    return typeof(storage[key]) !== 'undefined' ? storage[key] : null;
                },
                removeItem: function(key) {
                    delete storage[key];
                }
            };
        })({});
    }

    return {
        cookie: cookie,
        pad: pad,
        ago: ago,
        text: text,
        detext: detext,
        localStorageImpl: localStorageImpl
    };
});
