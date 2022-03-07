const config = require("app/config");

const bg = require("app/i18n/bg");
const cs = require("app/i18n/cs");
const da = require("app/i18n/da");
const de = require("app/i18n/de");
const en = require("app/i18n/en");
const fa = require("app/i18n/fa");
const fi = require("app/i18n/fi");
const fr = require("app/i18n/fr");
const hr = require("app/i18n/hr");
const hu = require("app/i18n/hu");
const ru = require("app/i18n/ru");
const it = require("app/i18n/it");
const ko = require("app/i18n/ko");
const eo = require("app/i18n/eo");
const oc = require("app/i18n/oc");
const pl = require("app/i18n/pl");
const pt_BR = require("app/i18n/pt_BR");
const pt_PT = require("app/i18n/pt_PT");
const sk = require("app/i18n/sk");
const sv = require("app/i18n/sv");
const nl = require("app/i18n/nl");
const el = require("app/i18n/el_GR");
const es = require("app/i18n/es");
const vi = require("app/i18n/vi");
const zh = require("app/i18n/zh_CN");
const zh_CN = require("app/i18n/zh_CN");
const zh_TW = require("app/i18n/zh_TW");

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

module.exports = {
    ago: ago,
    lang: lang,
    translate: translate,
    pluralize: pluralize,
};
