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
    var token = null;

    var statusChangeCallback = function(response) {
        if (response.status === "connected") {
            token = response.authResponse.accessToken;
            FB.api("/me", {fields: ["name", "email"]}, function(response) {
                state = states.loggedIn;
                authorData = {
                    uid: response["id"],
                    name: response["name"],
                    email: response["email"] || "",
                };
                localStorage.setItem("login_method", JSON.stringify("facebook"));
                isso.updateAllPostboxes();
                isso.clearPostboxNote();
            });
        } else {
            if (state === states.loadingSDK && manuallyLoadedSDK) {
                isso.showPostboxNote("Facebook");
            } else if (state === states.loggedIn) {
                localStorage.removeItem("login_method");
            }
            state = states.loggedOut;
            authorData = null;
            token = null;
            isso.updateAllPostboxes();
        }
    }

    var loadSDK = function() {
        state = states.loadingSDK;
        (function(d, s, id) {
            var js, fjs = d.getElementsByTagName(s)[0];
            if (d.getElementById(id)) return;
            js = d.createElement(s); js.id = id;
            js.src = "//connect.facebook.net/en_US/sdk.js";
            fjs.parentNode.insertBefore(js, fjs);
        }(document, "script", "facebook-jssdk"));
    }

    var init = function(isso_ref) {
        if (!config["facebook-enabled"]) {
            return;
        }

        isso = isso_ref;

        // Called when Facebook SDK has loaded
        window.fbAsyncInit = function() {
            FB.init({
                appId      : config["facebook-app-id"],
                cookie     : true,  // enable cookies to allow the server to access the session
                xfbml      : true,  // parse social plugins on this page
                version    : "v2.5" // use graph api version 2.5
            });

            FB.getLoginStatus(function(response) {
                statusChangeCallback(response);
            });
        };

        var method = JSON.parse(localStorage.getItem("login_method"));
        if (method == "facebook") {
            loadSDK();
        }
    }

    var updatePostbox = function(el) {
        if (state === states.loggedIn) {
            $(".auth-not-loggedin", el).hide();
            $(".auth-loggedin-facebook", el).showInline();
            $(".auth-facebook-name", el).innerHTML = authorData.name;
            $(".isso-postbox .avatar", el).setAttribute("src", "//graph.facebook.com/" + authorData.uid + "/picture");
            $(".isso-postbox .avatar", el).show();
        } else {
            $(".auth-loggedin-facebook", el).hide();
            $(".login-link-facebook", el).showInline();
            $(".login-link-facebook > img", el).setAttribute("src", api.endpoint + "/images/facebook-color.png");
        }
    }

    var initPostbox = function(el) {
        if (!config["facebook-enabled"]) {
            return;
        }
        updatePostbox(el);
        $(".logout-link-facebook", el).on("click", function() {
            FB.logout(function(response) {
                statusChangeCallback(response);
            });
        });
        $(".login-link-facebook", el).on("click", function() {
            if (state === states.inactive) {
                manuallyLoadedSDK = true;
                loadSDK();
            } else if (state === states.loggedOut)  {
                FB.login(function(response) {
                    statusChangeCallback(response);
                }, {scope: 'public_profile,email'});
            }
        });
    }

    var isLoggedIn = function() {
        return state === states.loggedIn;
    }

    var getAuthorData = function() {
        return {
            network: "facebook",
            id: authorData.uid,
            idToken: token,
            pictureURL: null,
            name: authorData.name,
            email: authorData.email,
            website: "",
        };
    }

    var prepareComment = function(comment) {
        comment.website = "//www.facebook.com/" + comment.auth_id;
        comment.pictureURL = "//graph.facebook.com/" + comment.auth_id + "/picture";
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
