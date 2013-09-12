/* Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 *
 * utility functions
 */

define({

    // return `cookie` string if set
    read: function(cookie) {
        return (document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2]
    },

    ago: function(date) {
    /*!
     * JavaScript Pretty Date
     * Copyright (c) 2011 John Resig (ejohn.org)
     * Licensed under the MIT and GPL licenses.
     */
    var diff = (((new Date()).getTime() - date.getTime()) / 1000),
        day_diff = Math.floor(diff / 86400);

    if (isNaN(day_diff) || day_diff < 0)
        return;

    return day_diff == 0 && (
        diff < 60 && "eben jetzt"  ||
            diff < 120 && "vor einer Minute" ||
            diff < 3600 && "vor " + Math.floor(diff / 60) + " Minuten" ||
            diff < 7200 && "vor einer Stunde" ||
            diff < 86400 && "vor " + Math.floor(diff / 3600) + " Stunden") ||
        day_diff == 1 && "Gestern" ||
        day_diff < 7 && "vor " + day_diff + " Tagen" ||
        day_diff < 31 && "vor " + Math.ceil(day_diff / 7) + " Wochen" ||
        day_diff < 365 && "vor " + Math.ceil(day_diff / 30) + " Monaten" ||
        "vor " + Math.ceil(day_diff / 365.25) + " Jahren";
    },

    heading: function() {
        /*
         * return first level heading that is probably the
         * blog title. If no h1 is found, "Untitled." is used.
         */
        var el = document.getElementById("isso-thread");
        var visited = [];

        var recurse = function(node) {
            for (var i = 0; i < node.childNodes.length; i++) {
                var child = node.childNodes[i];

                if (child.nodeType != child.ELEMENT_NODE) {
                    continue;
                }

                if (child.nodeName == "H1") {
                    return child;
                }

                if (visited.indexOf(child) == -1) {
                    return recurse(child);
                }
            }
        }

        while (true) {

            visited.push(el);

            if (el == document.documentElement) {
                break
            }

            var rv = recurse(el);
            if (rv) {
                return rv.textContent
            }

            el = el.parentNode;
        }

        return "Untitled."
    }
});