var requirejs = {
    paths: {
        text : "components/requirejs-text/text",
    },

    config: {
        text: {
            useXhr: function (url, protocol, hostname, port) {
                return true;
            }
        }
    }
};
