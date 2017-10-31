define(["app/config", "app/i18n/bg", "app/i18n/cs", "app/i18n/da",
        "app/i18n/de", "app/i18n/en", "app/i18n/fa", "app/i18n/fi",
        "app/i18n/fr", "app/i18n/hr", "app/i18n/ru", "app/i18n/it",
        "app/i18n/eo", "app/i18n/sv", "app/i18n/nl", "app/i18n/el_GR",
        "app/i18n/es", "app/i18n/vi", "app/i18n/zh_CN", "app/i18n/zh_CN", "app/i18n/zh_TW", "app/i18n/hu"],
        function(config, bg, cs, da, de, en, fa, fi, fr, hr, ru, it, eo, sv, nl, el, es, vi, zh, zh_CN, zh_TW) {

    "use strict";

    var pluralforms = function(lang) {
        switch (lang) {
        case "bg":
        case "cs":
        case "da":
        case "de":
        case "el":
        case "en":
        case "es":
        case "eo":
        case "fa":
        case "fi":
        case "hr":
        case "hu":
        case "it":
        case "sv":
        case "nl":
        case "vi":
        case "zh":
        case "zh_CN":
        case "zh_TW":
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
        bg: bg,
        cs: cs,
        da: da,
        de: de,
        el: el,
        en: en,
        eo: eo,
        es: es,
        fa: fa,
        fi: fi,
        fr: fr,
        it: it,
        hr: hr,
        hu: hu,
        ru: ru,
        sv: sv,
        nl: nl,
        vi: vi,
        zh: zh_CN,
        zh_CN: zh_CN,
        zh_TW: zh_TW
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
