define(['text', 'libjs-jade'], function (text, jade) {
    'use strict';

    return {
        load: function(name, req, onLoadNative, config) {
            var onload = function(content) {
                onLoadNative(jade.compileClient(content));
            };

            text.load(name + ".jade", req, onload, config);
        },
        write: function() {}
    };
});
