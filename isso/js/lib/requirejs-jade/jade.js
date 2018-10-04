define(function() {
    "use strict";

    var jade = null,
        builds = {};

    var fetchText = function() {
        throw new Error("Environment not supported.");
    };

    if (typeof process !== "undefined") {
        var fs = require.nodeRequire("fs");
        jade = require.nodeRequire("jade");
        fetchText = function(path, callback) {
            callback(fs.readFileSync(path, "utf-8"));
        };
    } else if ((typeof window !== "undefined" && window.navigator && window.document) || typeof importScripts !== "undefined") {
        fetchText = function (url, callback) {
            var xhr = new XMLHttpRequest();
            xhr.open('GET', url, true);
            xhr.onreadystatechange = function() {
                if (xhr.readyState === 4) {
                    callback(xhr.responseText);
                }
            };
            xhr.send(null);
        };
    }

    return {

        fetchText: fetchText,

        load: function(name, req, onload, config) {
            var path = req.toUrl(name + ".jade");
            fetchText(path, function(text) {
                if (jade === null) {
                    req(["libjs-jade"], function(jade) {
                        onload(jade.compileClient(text));
                        onload(text);
                    });
                } else {
                    builds[name] = jade.compileClient(text);
                    onload(builds[name]);
                }
            });

        },
        write: function(plugin, name, write) {
            if (builds.hasOwnProperty(name)) {
                write("define('" + plugin + "!" + name  +"', function () {" +
                      "  var wfn = function (jade) {" +
                      "    var fn = " + builds[name] + ";" +
                      "    return fn;" +
                      "  };" +
                      "wfn.compiled = true;" +
                      "return wfn;" +
                      "});\n");
            }
        }
    };
});
