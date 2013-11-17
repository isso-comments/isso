define(["app/config", "app/i18n/de", "app/i18n/en", "app/i18n/fr"], function(config, de, en, fr) {

    "use strict";

    // pluralization functions for each language you support
    var plurals = {
        "en": function (msgs, n) {
            return msgs[n === 1 ? 0 : 1];
        }
    };

    plurals["de"] = plurals["en"];
    plurals["fr"] = plurals["en"];

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
        fr: fr
    };
});
