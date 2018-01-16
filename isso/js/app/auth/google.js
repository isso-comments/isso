define(["app/dom", "app/config", "app/api"], function($, config, api) {

    "use strict";

    var isso = null;

    var states = {
        inactive: 0,
        loadingSDK: 1,
        loggedOut: 2,
        loggedIn: 3,
    };

    var state = states.inactive;
    var manuallyLoadedSDK = false;

    var authorData = null;
    var gAuth = null;

    var init = function(isso_ref) {
        if (!config["google-enabled"]) {
            return;
        }

        isso = isso_ref;

        var method = JSON.parse(localStorage.getItem("login_method"));
        if (method == "google") {
            loadSDK();
        }
    }

    var signedinChanged = function(signedin) {
        if (signedin) {
            var user = gAuth.currentUser.get();
            var profile = user.getBasicProfile();
            state = states.loggedIn;
            authorData = {
                uid: profile.getId(),
                name: profile.getName(),
                email: profile.getEmail() || "",
                pictureURL: profile.getImageUrl(),
                idToken: user.getAuthResponse().id_token,
            };
            localStorage.setItem("login_method", JSON.stringify("google"));
            isso.updateAllPostboxes();
            isso.clearPostboxNote();
        } else {
            if (state === states.loggedIn) {
                localStorage.removeItem("login_method");
            }
            state = states.loggedOut;
            authorData = null;
            isso.updateAllPostboxes();
        }
    }

    var loadSDK = function() {
        var gScriptEl = document.createElement("script");
        gScriptEl.src = "https://apis.google.com/js/platform.js";
        document.head.appendChild(gScriptEl);
        gScriptEl.addEventListener('load', function (e) {
            gapi.load('auth2', function() {
                gAuth = gapi.auth2.init({
                    client_id: config["google-client-id"],
                    cookiepolicy: "single_host_origin",
                });
                gAuth.isSignedIn.listen(signedinChanged)
                state = states.loggedOut;
                if (manuallyLoadedSDK) {
                    isso.showPostboxNote("Google+");
                }
                isso.updateAllPostboxes();
            });
        });
    }

    var updatePostbox = function(el) {
        if (state === states.loggedIn) {
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

    var initPostbox = function(el) {
        if (!config["google-enabled"]) {
            return;
        }
        updatePostbox(el);
        $(".logout-link-google", el).on("click", function() {
            gAuth.signOut();
        });
        $(".login-link-google", el).on("click", function() {
            if (state === states.inactive) {
                manuallyLoadedSDK = true;
                loadSDK();
            } else if (state === states.loggedOut) {
                gAuth.signIn();
            }
        });
    }

    var isLoggedIn = function() {
        return state === states.loggedIn;
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
