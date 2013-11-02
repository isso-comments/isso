define(["q"], function(Q) {

    "use strict";

    Q.stopUnhandledRejectionTracking();
    Q.longStackSupport = true;

    var endpoint = null, remote_addr = null,
        salt = "Eech7co8Ohloopo9Ol6baimi",
        location = window.location.pathname;

    var rules = {
        "/": [200, 404],
        "/new": [201, 202],
        "/id/\\d+": [200, 403, 404],
        "/id/\\d+/(like/dislike)": [200],
        "/count": [200]
    };

    // guess Isso API location
    var js = document.getElementsByTagName("script");
    for (var i = 0; i < js.length; i++) {
        if (js[i].src.match("/js/components/requirejs/require\\.js$")) {
            endpoint = js[i].src.substring(0, js[i].src.length - 35);
            break;
        } else if (js[i].src.match("/js/(embed|count)\\.(min|dev)\\.js$")) {
            endpoint = js[i].src.substring(0, js[i].src.length - 16);
            break;
        }
    }

    if (! endpoint) {
        throw "no Isso API location found";
    }

    var curl = function(method, url, data) {

        var xhr = new XMLHttpRequest();
        var response = Q.defer();

        function onload() {

            var rule = url.replace(endpoint, "").split("?", 1)[0];

            if (rule in rules && rules[rule].indexOf(xhr.status) === -1) {
                response.reject(xhr.responseText);
            } else {
                response.resolve({status: xhr.status, body: xhr.responseText});
            }
        }

        try {
            xhr.open(method, url, true);
            xhr.withCredentials = true;  // fuck you, fuck you, fuck you IE
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
        var rv = "";
        for (var key in params) {
            if (params.hasOwnProperty(key) && params[key]) {
                rv += key + "=" + encodeURIComponent(params[key]) + "&";
            }
        }

        return rv.substring(0, rv.length - 1);  // chop off trailing "&"
    };

    var create = function(data) {
        return curl("POST", endpoint + "/new?" + qs({uri: location}), JSON.stringify(data)).then(
            function (rv) { return JSON.parse(rv.body); });
    };

    var modify = function(id, data) {
        return curl("PUT", endpoint + "/id/" + id, JSON.stringify(data)).then(
            function (rv) { return JSON.parse(rv.body); });
    };

    var remove = function(id) {
        return curl("DELETE", endpoint + "/id/" + id, null).then(function(rv) {
            if (rv.status === 403) {
                throw "Not authorized to remove this comment!";
            }

            return JSON.parse(rv.body) === null;
        });
    };

    var view = function(id, plain) {
        return curl("GET", endpoint + "/id/" + id + "?" + qs({plain: plain}), null).then(function (rv) {
            return JSON.parse(rv.body);
        });
    };

    var fetch = function(plain) {

        return curl("GET", endpoint + "/?" + qs({uri: location, plain: plain}), null).then(function (rv) {
            if (rv.status === 200) {
                return JSON.parse(rv.body);
            } else {
                return [];
            }
        });
    };

    var count = function(uri) {
        return curl("GET", endpoint + "/count?" + qs({uri: uri}), null).then(function(rv) {
            return JSON.parse(rv.body);
        });
    };

    var like = function(id) {
        return curl("POST", endpoint + "/id/" + id + "/like", null).then(function(rv) {
            return JSON.parse(rv.body);
        });
    };

    var dislike = function(id) {
        return curl("POST", endpoint + "/id/" + id + "/dislike", null).then(function(rv) {
            return JSON.parse(rv.body);
        });
    };

    remote_addr = curl("GET", endpoint + "/check-ip", null).then(function(rv) {
        return rv.body;
    });

    return {
        endpoint: endpoint,
        remote_addr: remote_addr,
        salt: salt,

        create: create,
        modify: modify,
        remove: remove,
        view: view,
        fetch: fetch,
        count: count,
        like: like,
        dislike: dislike
    };
});
