define(function() {

    "use strict";

    var stderr = function(text) { console.log(text); };

    var Promise = function() {
        this.success = [];
        this.errors = [];
    };

    Promise.prototype.then = function(onSuccess, onError) {
        this.success.push(onSuccess);
        if (onError) {
            this.errors.push(onError);
        } else {
            this.errors.push(stderr);
        }
    };

    var Defer = function() {
        this.promise = new Promise();
    };

    Defer.prototype = {
        promise: Promise,
        resolve: function(rv) {
            this.promise.success.forEach(function(callback) {
                window.setTimeout(function() {
                    callback(rv);
                }, 0);
            });
        },

        reject: function(error) {
            this.promise.errors.forEach(function(callback) {
                window.setTimeout(function() {
                    callback(error);
                }, 0);
            });
        }
    };

    var when = function(obj, func) {
        if (obj instanceof Promise) {
            return obj.then(func);
        } else {
            return func(obj);
        }
    };

    return {
        defer: function() { return new Defer(); },
        when: when
    };

});
