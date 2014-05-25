var requirejs = {
    paths: {
        "text": "components/requirejs-text/text",
        "libjs-jade": "components/jade/jade",
        "libjs-jade-runtime": "components/jade/runtime",
        "jade": "lib/requirejs-jade/jade"
    },

    config: {
        text: {
            useXhr: function (url, protocol, hostname, port) {
                return true;
            }
        }
    }
};
