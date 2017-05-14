define(["app/dom", "app/config", "app/api"], function($, config, api) {

    "use strict";

    var isso = null;
    var loadedSDK = false;
    var loggedIn = false;
    var authorData = null;
    var gAuth = null;

    var init = function(isso_ref) {
        if (!config["google-enabled"]) {
            return;
        }

        isso = isso_ref;

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
                gAuth.isSignedIn.listen(signedinChanged)
                loadedSDK = true;
                isso.updateAllPostboxes();
            });
        });

    }

    var signedinChanged = function(signedin) {
        if (signedin) {
            var user = gAuth.currentUser.get();
            var profile = user.getBasicProfile();
            loggedIn = true;
            authorData = {
                uid: profile.getId(),
                name: profile.getName(),
                email: profile.getEmail() || "",
                pictureURL: profile.getImageUrl(),
                idToken: user.getAuthResponse().id_token,
            };
            isso.updateAllPostboxes();
        } else {
            loggedIn = false;
            authorData = null;
            isso.updateAllPostboxes();
        }
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
                $(".auth-loggedin-google", el).hide();
                $(".login-link-google", el).showInline();
                $(".login-link-google > img", el).setAttribute("src", api.endpoint + "/images/googleplus-color.png");
            }
        }
    }

    var initPostbox = function(el) {
        if (!config["google-enabled"]) {
            return;
        }
        updatePostbox(el);
        $(".logout-link-google", el).on("click", function() {
            gAuth.signOut();
        });
        $(".login-link-google", el).on("click", function() {
            gAuth.signIn();
        });
    }

    var isLoggedIn = function() {
        return loggedIn;
    }

    var getAuthorData = function() {
        return {
            network: "google",
            id: authorData.uid,
            idToken: authorData.idToken,
            pictureURL: authorData.pictureURL,
            name: authorData.name,
            email: authorData.email,
            website: "",
        };
    }

    var prepareComment = function(comment) {
        comment.website = "//plus.google.com/" + comment.auth_id + "/posts";
    }

    return {
        init: init,
        initPostbox: initPostbox,
        updatePostbox: updatePostbox,
        isLoggedIn: isLoggedIn,
        getAuthorData: getAuthorData,
        prepareComment: prepareComment
    };

});
