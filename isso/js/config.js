var requirejs = {
    paths: {
        "text": "../../node_modules/requirejs-text/text",
        "jade": "lib/requirejs-jade/jade",
        "libjs-jade": "../../node_modules/jade/jade",
        "libjs-jade-runtime": "../../node_modules/jade/runtime"
    },

    config: {
        text: {
            useXhr: function (url, protocol, hostname, port) {
                return true;
            }
        }
    }
};
