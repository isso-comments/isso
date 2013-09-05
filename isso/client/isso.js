/* Isso – Ich schrei sonst!
 *
 * Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 */

// Uhm. Namespaces are one honking great idea, aren't they?
var isso = {};


var init = function() {
    var isso = new Object();

    // guess Isso API location
    var js = document.getElementsByTagName("script");
    for (var i = 0; i < js.length; i++) {
        if (js[i].src.match("/client/require\\.js$")) {
            isso.location = js[i].src.substring(0, 18);
            break;
        }
    }

    console.log(isso.location)
}


isso.create = function(data, func) {

    var request = new XMLHttpRequest();

//    $.ajax('POST', prefix + '/1.0/' + isso.path + '/new',
//        JSON.stringify(data), {'Content-Type': 'application/json'}).then(func);
};


isso.modify = function(id, data, func) {
    if (!verify(data)) {
        return;
    }

    $.ajax('PUT', prefix + '/1.0/' + isso.path + '/' + id,
    JSON.stringify(data), {'Content-Type': 'application/json'}).then(func)
};


isso.plain = function(id, func) {
    $.ajax('GET', prefix + '/1.0/' + isso.path + '/' + id, {'plain': '1'}).then(func);
}


isso.remove = function(id, func) {
    $.ajax('DELETE', prefix + '/1.0/' + isso.path + '/' + id).then(func);
}


isso.approve = function (id, func) {
    $.ajax('PUT', '/1.0/' + isso.path + '/' + id + '/approve').then(func)
}
