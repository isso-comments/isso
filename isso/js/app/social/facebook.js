define(["app/dom", "app/api"], function($, api) {

    "use strict";

    var loadedSDK = false;
    var loggedIn = false;
    var authorData = null;

    var statusChangeCallback = function(response) {
        if (response.status === "connected") {
            FB.api("/me", function(response) {
                loggedIn = true;
                authorData = {
                    name: response["name"],
                };
                updateAllPostboxes();
            });
        } else {
            loggedIn = false;
            authorData = null;
            updateAllPostboxes();
        }

    }

    var init = function() {

        // Called when Facebook SDK has loaded
        window.fbAsyncInit = function() {
            FB.init({
                appId      : "1561583880825335",
                cookie     : true,  // enable cookies to allow the server to access the session
                xfbml      : true,  // parse social plugins on this page
                version    : "v2.5" // use graph api version 2.5
            });

            loadedSDK = true;

            FB.getLoginStatus(function(response) {
                statusChangeCallback(response);
            });
        };

        // Load Facebook SDK
        (function(d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            js = d.createElement(s); js.id = id;
            js.src = "//connect.facebook.net/en_US/sdk.js";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, "script", "facebook-jssdk"));

    }

    var updatePostbox = function(el) {
        if (loadedSDK) {
            if (loggedIn) {
                $(".auth-not-loggedin", el).hide();
                $(".auth-loggedin-facebook", el).showInline();
                $(".auth-facebook-name", el).innerHTML = authorData.name;
            } else {
                $(".auth-not-loggedin", el).showInline();
                $(".auth-loggedin-facebook", el).hide();
                $(".social-login-link-facebook", el).showInline();
                $(".social-login-link-facebook > img", el).setAttribute("src", api.endpoint + "/images/facebook-color.png");
            }
        }
    }

    var updateAllPostboxes = function() {
        $.eachByClass("isso-postbox", function(el) {
            updatePostbox(el);
        });
    }

    var initPostbox = function(el) {
        updatePostbox(el);
        $(".social-logout-link-facebook", el).on("click", function() {
            FB.logout(function(response) {
                statusChangeCallback(response);
            });
        });
        $(".social-login-link-facebook", el).on("click", function() {
            FB.login(function(response) {
                statusChangeCallback(response);
            });
        });
    }

    return {
        init: init,
        initPostbox: initPostbox
    };

});
