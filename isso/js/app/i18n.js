define(["app/config", "app/i18n/bg", "app/i18n/cs", "app/i18n/da",
        "app/i18n/de", "app/i18n/en", "app/i18n/fa", "app/i18n/fi",
        "app/i18n/fr", "app/i18n/hr",  "app/i18n/hu", "app/i18n/ru", "app/i18n/it", "app/i18n/ko",
        "app/i18n/eo", "app/i18n/oc", "app/i18n/pl", "app/i18n/pt_BR", "app/i18n/pt_PT", "app/i18n/sk", "app/i18n/sv", "app/i18n/nl", "app/i18n/el_GR",
        "app/i18n/es", "app/i18n/vi", "app/i18n/zh_CN", "app/i18n/zh_CN", "app/i18n/zh_TW"],
        function(config, bg, cs, da, de, en, fa, fi, fr, hr, hu, ru, it, ko, eo, oc, pl, pt_BR, pt_PT, sk, sv, nl, el, es, vi, zh, zh_CN, zh_TW) {

    "use strict";

    var pluralforms = function(lang) {
        // we currently only need to look at the primary language
        // subtag.
        switch (lang.split("-", 1)[0]) {
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
        case "ko":
        case "pt":
        case "sv":
        case "nl":
        case "vi":
        case "zh":
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
        case "oc":
            return function(msgs, n) {
                return msgs[n > 1 ? 1 : 0];
            };
        case "pl":
            return function(msgs, n) {
                if (n === 1) {
                    return msgs[0];
                } else if (n % 10 >= 2 && n % 10 <= 4 && (n % 100 < 10 || n % 100 >= 20)) {
                    return msgs[1];
                } else {
                    return typeof msgs[2] !== "undefined" ? msgs[2] : msgs[1];
                }
            };
        case "sk":
            return function(msgs, n) {
                if (n === 1) {
                    return msgs[0];
                } else if (n === 2 || n === 3 || n === 4) {
                    return msgs[1];
                } else {
                    return typeof msgs[2] !== "undefined" ? msgs[2] : msgs[1];
                }
            };
        default:
            return null;
        }
    };

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
        ko: ko,
        hr: hr,
        hu: hu,
        oc: oc,
        pl: pl,
        pt: pt_BR,
        "pt-BR": pt_BR,
        "pt-PT": pt_PT,
        ru: ru,
        sk: sk,
        sv: sv,
        nl: nl,
        vi: vi,
        zh: zh_CN,
        "zh-CN": zh_CN,
        "zh-TW": zh_TW
    };

    // for each entry in config.langs, see whether we have a catalogue
    // entry and a pluralforms entry for it.  if we don't, try chopping
    // off everything but the primary language subtag, before moving
    // on to the next one.
    var lang, plural, translations;
    for (var i = 0; i < config.langs.length; i++) {
        lang = config.langs[i];
        plural = pluralforms(lang);
        translations = catalogue[lang];
        if (plural && translations)
            break;
        if (/-/.test(lang)) {
            lang = lang.split("-", 1)[0];
            plural = pluralforms(lang);
            translations = catalogue[lang];
            if (plural && translations)
                break;
        }
    }

    // absolute backstop; if we get here there's a bug in config.js
    if (!plural || !translations) {
        lang = "en";
        plural = pluralforms(lang);
        translations = catalogue[lang];
    }

    var translate = function(msgid) {
        return config[msgid + '-text-' + lang] ||
          translations[msgid] ||
          en[msgid] ||
          "[?" + msgid + "]";
    };

    var pluralize = function(msgid, n) {
        var msg;

        msg = translate(msgid);
        if (msg.indexOf("\n") > -1) {
            msg = plural(msg.split("\n"), (+ n));
        }

        return msg ? msg.replace("{{ n }}", (+ n)) : msg;
    };

    var ago = function(localTime, date) {

        var secs = ((localTime.getTime() - date.getTime()) / 1000);

        if (isNaN(secs) || secs < 0 ) {
            secs = 0;
        }

        var mins = Math.floor(secs / 60), hours = Math.floor(mins / 60),
            days = Math.floor(hours / 24);

        return secs  <=  45 && translate("date-now")  ||
               secs  <=  90 && pluralize("date-minute", 1) ||
               mins  <=  45 && pluralize("date-minute", mins) ||
               mins  <=  90 && pluralize("date-hour", 1) ||
               hours <=  22 && pluralize("date-hour", hours) ||
               hours <=  36 && pluralize("date-day", 1) ||
               days  <=   5 && pluralize("date-day", days) ||
               days  <=   8 && pluralize("date-week", 1) ||
               days  <=  21 && pluralize("date-week", Math.floor(days / 7)) ||
               days  <=  45 && pluralize("date-month", 1) ||
               days  <= 345 && pluralize("date-month", Math.floor(days / 30)) ||
               days  <= 547 && pluralize("date-year", 1) ||
                               pluralize("date-year", Math.floor(days / 365.25));
    };

    return {
        ago: ago,
        lang: lang,
        translate: translate,
        pluralize: pluralize
    };
});
