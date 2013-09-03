/* Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 *
 * utility functions -- JS Y U SO STUPID?
 *
 * read(cookie):  return `cookie` string if set
 * format(date):  human-readable date formatting
 * brew(array):   similar to DOMinate essentials
 */

 function read(cookie) {
    return (document.cookie.match('(^|; )' + cookie + '=([^;]*)') || 0)[2]
};


function format(date) {
    /*!
     * JavaScript Pretty Date
     * Copyright (c) 2011 John Resig (ejohn.org)
     * Licensed under the MIT and GPL licenses.
     */
    var diff = (((new Date()).getTime() - date.getTime()) / 1000),
        day_diff = Math.floor(diff / 86400);

    if (isNaN(day_diff) || day_diff < 0 || day_diff >= 31)
        return;

    return day_diff == 0 && (
            diff < 60 && "just now" ||
            diff < 120 && "1 minute ago" ||
            diff < 3600 && Math.floor(diff / 60) + " minutes ago" ||
            diff < 7200 && "1 hour ago" ||
            diff < 86400 && Math.floor(diff / 3600) + " hours ago") ||
        day_diff == 1 && "Yesterday" ||
        day_diff < 7 && day_diff + " days ago" ||
        day_diff < 31 && Math.ceil(day_diff / 7) + " weeks ago";
}


function brew(arr) {
    /*
     * Element creation utility.  Similar to DOMinate, but with a slightly different syntax:
     * brew([TAG, {any: attribute, ...}, 'Hello World', ' Foo Bar', ['TAG', 'Hello World'], ...])
     * --> <TAG any="attribute">Hello World Foo Bar<TAG>Hello World</TAG></TAG>
     */

    var rv = document.createElement(arr[0]);

    for (var i = 1; i < arr.length; i++) {

        if (arr[i] instanceof Array) {
            rv.appendChild(brew(arr[i]));
        } else if (typeof(arr[i]) == "string") {
            rv.appendChild(document.createTextNode(arr[i]));
        } else {
            attrs = arr[i] || {};
            for (var k in attrs) {
                if (!attrs.hasOwnProperty(k)) continue;
                rv.setAttribute(k, attrs[k]);
            }
        }
    };

   return rv;
}
