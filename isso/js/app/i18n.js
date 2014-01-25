define(["app/config", "app/i18n/de", "app/i18n/en", "app/i18n/fr", "app/i18n/ru", "app/i18n/it"], function(config, de, en, fr, ru, it) {

    "use strict";

    // pluralization functions for each language you support
    var plurals = {
        "en": function(msgs, n) {
            return msgs[n === 1 ? 0 : 1];
        },
        "fr": function(msgs, n) {
            return msgs[n > 1 ? 1 : 0]
        },
        "ru": function(msg, n) {
            if (n % 10 === 1 && n % 100 !== 11) {
                return msg[0];
            } else if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) {
                return msg[1];
            } else {
                return msg[2] !== undefined ? msg[2] : msg[1];
            }
        }
    };

    plurals["de"] = plurals["en"];
    plurals["it"] = plurals["en"];

    // useragent's prefered language (or manually overridden)
    var lang = config.lang;

    // fall back to English
    if (!plurals[lang]) {
        lang = "en";
    }

    return {
        plurals: plurals,
        lang: lang,
        de: de,
        en: en,
        fr: fr,
        ru: ru,
        it: it
    };
});
