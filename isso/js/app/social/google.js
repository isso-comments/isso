define(["app/dom", "app/api"], function($, api) {

    "use strict";

    var loadedSDK = false;
    var loggedIn = false;
    var authorData = null;
    var gAuth = null;

    var init = function() {

        // Load Google API
        var gScriptEl = document.createElement("script");
        gScriptEl.src = "https://apis.google.com/js/platform.js";
        document.head.appendChild(gScriptEl);
        gScriptEl.addEventListener('load', function (e) {
            gapi.load('auth2', function() {
                gAuth = gapi.auth2.init({
                    client_id: "41900040914-qfuks55vr812m25vtpkrq6lbahfgg151.apps.googleusercontent.com",
                    cookiepolicy: "single_host_origin",
                });
                loadedSDK = true;
                updateAllPostboxes();
            });
        });

    }

    var updatePostbox = function(el) {
        if (loadedSDK) {
            if (loggedIn) {
                $(".auth-not-loggedin", el).hide();
                $(".auth-loggedin-google", el).showInline();
                $(".auth-google-name", el).innerHTML = authorData.name;
                $(".isso-postbox .avatar", el).setAttribute("src", authorData.pictureURL);
                $(".isso-postbox .avatar", el).show();
            } else {
                $(".auth-not-loggedin", el).showInline();
                $(".auth-loggedin-google", el).hide();
                $(".social-login-link-google", el).showInline();
                $(".social-login-link-google > img", el).setAttribute("src", api.endpoint + "/images/googleplus-color.png");
                $(".isso-postbox .avatar", el).hide();
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
        $(".social-logout-link-google", el).on("click", function() {
            gAuth.signOut().then(function() {
                loggedIn = false;
                authorData = null;
                updateAllPostboxes();
            });
        });
        $(".social-login-link-google", el).on("click", function() {
            gAuth.signIn().then(function(googleUser) {
                var profile = googleUser.getBasicProfile();
                loggedIn = true;
                console.log(profile.getId());
                authorData = {
                    uid: profile.getId(),
                    name: profile.getName(),
                    email: profile.getEmail() || "",
                    pictureURL: profile.getImageUrl(),
                };
                updateAllPostboxes();
            });
        });
    }

    var isLoggedIn = function() {
        return loggedIn;
    }

    return {
        init: init,
        initPostbox: initPostbox,
        isLoggedIn: isLoggedIn
    };

});
