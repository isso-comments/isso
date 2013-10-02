define(["app/i18n/de", "app/i18n/en"], function(de, en) {

    "use strict";

    // pluralization functions for each language you support
    var plurals = {
        "en": function (msgs, n) {
            return msgs[n === 1 ? 0 : 1];
        }
    };

    plurals["de"] = plurals["en"];

    // the user's language. you can replace this with your own code
    var lang = (navigator.language || navigator.userLanguage).split("-")[0];

    // fall back to English
    if (!plurals[lang]) {
        lang = "en";
    }

    return {
        plurals: plurals,
        lang: lang,
        de: de,
        en: en
    };
});
