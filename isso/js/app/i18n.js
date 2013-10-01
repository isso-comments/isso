define(function() {

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
        de: {
            "postbox-text" : "Kommentar hier eintippen (mindestens 3 Zeichen)",
            "postbox-author" : "Name (optional)",
            "postbox-email" : "Email (optional)",
            "postbox-submit": "Abschicken.",

            "num-comments": "1 Kommentar\n{{ n }} Kommentare",
            "no-comments": "Keine Kommentare bis jetzt",

            "comment-reply": "Antworten",
            "comment-delete": "Löschen",
            "comment-confirm": "Bestätigen",
            "comment-close": "Schließen",

            "date-now": "eben jetzt",
            "date-minute": "vor einer Minute\nvor {{ n }} Minuten",
            "date-hour": "vor einer Stunde\nvor {{ n }} Stunden",
            "date-day": "Gestern\nvor {{ n }} Tagen",
            "date-week": "letzte Woche\nvor {{ n }} Wochen",
            "date-month": "letzten Monat\nvor {{ n }} Monaten",
            "date-year": "letztes Jahr\nvor {{ n }} Jahren"
        },
        en: {
            "postbox-text": "Type Comment Here (at least 3 chars)",
            "postbox-author": "Name (optional)",
            "postbox-email": "E-mail (optional)",
            "postbox-submit": "Post Comment.",

            "num-comments": "One Comment\n{{ n }} Comments",
            "no-comments": "No Comments Yet",

            "comment-reply": "Reply",
            "comment-delete": "Delete",
            "comment-confirm": "Confirm",
            "comment-close": "Close",

            "date-now": "now",
            "date-minute": "a minute ago\n{{ n }} minutes ago",
            "date-hour": "an hour ago\n{{ n }} hours ago",
            "date-day": "Yesterday\n{{ n }} days ago",
            "date-week": "last week\n{{ n }} weeks ago",
            "date-month": "last month\n{{ n }} months ago",
            "date-year": "last year\n{{ n }} years ago"
        }
    };
});
