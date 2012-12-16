/* Isso – Ich schrei sonst!
 *
 * Copyright 2012, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 *
 *
 * Code requires Bean, Bonzo, Qwery, domReady (all are part of jeesh) and
 * reqwest. To ease integration with websites, all classes are prefixed
 * with `isso`.
 */

// Uhm. Namespaces are one honking great idea, aren't they?
var isso = isso || {},
    prefix = "",
    path = encodeURIComponent(window.location.pathname);

// XXX
isso.prefix = prefix;
isso.path = path;


/*
 * isso specific helpers to create, modify, remove and receive comments
 */

function verify(data) {
    return data['text'] == null ? false : true
};


isso.create = function(data, func) {

    if (!verify(data)) {
        return;
    }

    $.ajax('POST', prefix + '/1.0/' + path + '/new',
        JSON.stringify(data), {'Content-Type': 'application/json'}).then(func);
};


isso.modify = function(id, data, func) {
    if (!verify(data)) {
        return;
    }

    $.ajax('PUT', prefix + '/1.0/' + path + '/' + id,
    JSON.stringify(data), {'Content-Type': 'application/json'}).then(func)
};


isso.plain = function(id, func) {
    $.ajax('GET', prefix + '/1.0/' + path + '/' + id, {'plain': '1'}).then(func);
}


isso.remove = function(id, func) {
    $.ajax('DELETE', prefix + '/1.0/' + path + '/' + id).then(func);
}
