/*
 * Copyright 2013, Martin Zimmermann <info@posativ.org>. All rights reserved.
 * License: BSD Style, 2 clauses. See isso/__init__.py.
 */

define(["lib/q", "app/models"], function(Q, models) {

    // http://stackoverflow.com/questions/17544965/unhandled-rejection-reasons-should-be-empty
    Q.stopUnhandledRejectionTracking();
    Q.longStackSupport = true;

    var endpoint = null,
        location = window.location.pathname;

    // guess Isso API location
    var js = document.getElementsByTagName("script");
    for (var i = 0; i < js.length; i++) {
        if (js[i].src.match("/client/require\\.js$")) {
            endpoint = js[i].src.substring(0, js[i].src.length - 18);
            break;
        }

        throw "no Isso API location found";
    }

    var curl = function(method, url, data) {

        var request = new XMLHttpRequest();
        var response = Q.defer();

        function onload() {
            response.resolve({status: request.status, body: request.responseText});
        }

        try {
            request.open(method, url, true);
            request.overrideMimeType("application/javascript");

            request.onreadystatechange = function () {
                if (request.readyState === 4) {
                    onload();
                }
            };
        } catch (exception) {
            response.reject(exception.message);
        }

        request.send(data);
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
        return curl("DELETE", endpoint + "/?" + qs({uri: location, id: id}), null)
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

    return {
        endpoint: endpoint,
        create: create,
        remove: remove,
        fetchall: fetchall
    }

});