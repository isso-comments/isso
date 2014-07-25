define(function() {
    "use strict";

    // 2011/01/01 in UTC
    var epoch = 1293840000;

    var decode = function(str) {
        return atob(str + new Array(4 - str.length % 4 + 1).join("="));
    };

    var timestamp = function(str) {
        var bytes = [];
        for (var i = 0; i < str.length; i++) {
            bytes.push(str.charCodeAt(i));
        }

        var a = 0;
        for (var j = 0; j < bytes.length; j++) {
            a = a << 8 | +bytes[j];
        }

        return a + epoch;
    };

    /*
     * Load data signed with itsdangerous' URLSafeTimedSerializer.
     *
     * If no signature was found or the payload has been expired, return
     * `null`. Otherwise, return unserialized datastructure.
     */
    return function(val, max_age) {

        var _ = val.split(".", 3),
            payload = _[0], ts = _[1], signature = _[2];

        if (typeof signature === "undefined") {
            return null;
        }

        var age = (new Date()).getTime() / 1000 - timestamp(decode(ts));
        if (typeof max_age !== "undefined" && age > max_age) {
            return null;
        }

        return JSON.parse(decode(payload));
    };
});