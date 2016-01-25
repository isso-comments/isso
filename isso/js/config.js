var requirejs = {
    paths: {
        "text": "components/text/text",
        "jade": "lib/requirejs-jade/jade",
        "libjs-jade": "components/jade/jade",
        "libjs-jade-runtime": "components/jade/runtime"
    },

    config: {
        text: {
            useXhr: function (url, protocol, hostname, port) {
                return true;
            }
        }
    }
};
