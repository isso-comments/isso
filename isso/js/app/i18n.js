define(["app/config", "app/i18n/de", "app/i18n/en", "app/i18n/fr", "app/i18n/ru", "app/i18n/it", "app/i18n/eo", "app/i18n/sv", "app/i18n/nl", "app/i18n/es"], function(config, de, en, fr, ru, it, eo, sv, nl, es) {

    "use strict";

    var pluralforms = function(lang) {
        switch (lang) {
        case "de":
        case "en":
        case "es":
        case "eo":
        case "it":
        case "sv":
        case "nl":
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
        eo: eo,
        fr: fr,
        it: it,
        ru: ru,
        sv: sv,
        nl: nl,
        es: es
    };

    var plural = pluralforms(lang);

    var translate = function(msgid) {
        return catalogue[lang][msgid] || en[msgid] || "???";
    };

    var pluralize = function(msgid, n) {
        var msg;

        msg = translate(msgid);
        if (msg.indexOf("\n") > -1) {
            msg = plural(msg.split("\n"), (+ n));
        }

        return msg ? msg.replace("{{ n }}", (+ n)) : msg;
    };

    return {
        lang: lang,
        translate: translate,
        pluralize: pluralize
    };
});
