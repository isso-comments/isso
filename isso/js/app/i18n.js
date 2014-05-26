define(["app/config", "app/i18n/de", "app/i18n/en", "app/i18n/fr", "app/i18n/ru", "app/i18n/it"], function(config, de, en, fr, ru, it) {

    "use strict";

    var pluralforms = function(lang) {
        switch (lang) {
        case "en":
        case "de":
        case "it":
            return function(msgs, n) {
                return msgs[n === 1 ? 0 : 1];
            };
        case "fr":
            return function(msgs, n) {
                return msgs[n > 1 ? 1 : 0];
            };
        case "ru":
            return function(msgs, n) {
                if (n % 10 === 1 && n % 100 !== 11) {
                    return msgs[0];
                } else if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) {
                    return msgs[1];
                } else {
                    return typeof msgs[2] !== "undefined" ? msgs[2] : msgs[1];
                }
            };
        default:
            return null;
        }
    };

    // useragent's prefered language (or manually overridden)
    var lang = config.lang;

    // fall back to English
    if (! pluralforms(lang)) {
        lang = "en";
    }

    var catalogue = {
        de: de,
        en: en,
        fr: fr,
        ru: ru,
        it: it
    };

    var plural = pluralforms(lang);

    var translate = function(msgid) {
        return catalogue[lang][msgid] || en[msgid] || "???";
    };

    var pluralize = function(msgid, n) {
        var msg;

        msg = translate(msgid);
        msg = plural(msg.split("\n"), (+ n));

        return msg ? msg.replace("{{ n }}", (+ n)) : msg;
    };

    return {
        lang: lang,
        translate: translate,
        pluralize: pluralize
    };
});
