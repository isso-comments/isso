/*
 * Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 */

define(["lib/q"], function(Q) {

    // http://stackoverflow.com/questions/17544965/unhandled-rejection-reasons-should-be-empty
    Q.stopUnhandledRejectionTracking();
    Q.longStackSupport = true;

    var endpoint = null,
        location = window.location.pathname;

    // guess Isso API location
    var js = document.getElementsByTagName("script");
    for (var i = 0; i < js.length; i++) {
        if (js[i].src.match("/js/require\\.js$")) {
            endpoint = js[i].src.substring(0, js[i].src.length - 14);
            break;
        } else if (js[i].src.match("/js/embed\\.min\\.js$")) {
            endpoint = js[i].src.substring(0, js[i].src.length - 16);
            break;
        }
    }

    if (endpoint == null) {
        throw "no Isso API location found";
    }

    var curl = function(method, url, data) {

        var xhr = new XMLHttpRequest();
        var response = Q.defer();

        if (! ("withCredentials" in xhr)) {
            respone.reject("I won't support IE ≤ 10.")
            return response.promise;
        }

        xhr.withCredentials = true;

        function onload() {
            response.resolve({status: xhr.status, body: xhr.responseText});
        }

        try {
            xhr.open(method, url, true);
            xhr.overrideMimeType("application/javascript");

            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    onload();
                }
            };
        } catch (exception) {
            response.reject(exception.message);
        }

        xhr.send(data);
        return response.promise;
    };

    var qs = function(params) {
        rv = "";
        for (var key in params) {
            if (params.hasOwnProperty(key)) {
                rv += key + "=" + encodeURIComponent(params[key]) + "&";
            }
        }

        return rv.substring(0, rv.length - 1)  // chop off trailing "&"
    }

    var create = function(data) {

        return curl("POST", endpoint + "/new?" + qs({uri: location}), JSON.stringify(data))
        .then(function (rv) {
            if (rv.status == 201 || rv.status == 202) {
                return JSON.parse(rv.body);
            } else {
                msg = rv.body.match("<p>(.+)</p>")
                throw {status: rv.status, reason: (msg && msg[1]) || rv.body}
            }
        })
    }

    var modify = function(data) {
        // ...
    }

    var remove = function(id) {
        return curl("DELETE", endpoint + "/id/" + id, null)
        .then(function(rv) {
            if (rv.status == 200) {
                return JSON.parse(rv.body) == null;
            } else {
                    throw {status: rv.status, reason: rv.body}
            }
        })
    }

    var fetchall = function() {

        return curl("GET", endpoint + "/?" + qs({uri: location}), null)
        .then(function (rv) {
            if (rv.status == 200) {
                return JSON.parse(rv.body)
            } else {
                msg = rv.body.match("<p>(.+)</p>")
                throw {status: rv.status, reason: (msg && msg[1]) || rv.body}
            }
        })
    }

    var count = function(uri) {
        return curl("GET", endpoint + "/count?" + qs({uri: uri}), null)
        .then(function (rv) {
            if (rv.status == 200)
                return JSON.parse(rv.body)

            throw {status: rv.status, reason: rv.body};
        })
    }

    return {
        endpoint: endpoint,
        create: create,
        remove: remove,
        fetchall: fetchall,
        count: count
    }

});