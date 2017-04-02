define(["app/dom", "app/config", "app/api", "app/jade", "app/i18n"], function($, config, api, jade, i18n) {

    "use strict";

    var isso = null;
    var loggedIn = false;
    var sessionID = null;
    var authorData = null;

    var init = function(isso_ref) {
        if (!config["openid-enabled"]) {
            return;
        }
        isso = isso_ref;
        window.addEventListener("message", function(event) {
            var origin = event.origin || event.originalEvent.origin;
            if (origin != api.endpoint)
                return;
            loggedIn = true;
            sessionID = event.data.state;
            authorData = {
                name: event.data.name,
                email: event.data.email,
                pictureURL: event.data.picture,
                website: event.data.website,
            };
            isso.updateAllPostboxes();
        }, false);
    }

    var updatePostbox = function(el) {
        if (!config["openid-enabled"]) {
            return;
        }
        if (loggedIn) {
            $(".auth-not-loggedin", el).hide();
            $(".auth-loggedin-openid", el).showInline();
            $(".auth-openid-name", el).innerHTML = authorData.name;
            if (authorData.pictureURL)
                $(".isso-postbox .avatar", el).setAttribute("src", authorData.pictureURL);
            else
                $(".isso-postbox .avatar", el).hide();
            $(".isso-postbox .avatar", el).show();
        } else {
            $(".auth-loggedin-openid", el).hide();
            $(".social-login-link-openid", el).showInline();
            $(".social-login-link-openid > img", el).setAttribute("src", api.endpoint + "/images/openid-icon-32x32.png");
        }
    }

    var initPostbox = function(el) {
        if (!config["openid-enabled"]) {
            return;
        }
        updatePostbox(el);
        $(".social-logout-link-openid", el).on("click", function() {
            api.openidLogout(sessionID);
            loggedIn = false;
            sessionID = null;
            authorData = null;
            isso.updateAllPostboxes();
        });
        $(".social-login-link-openid", el).on("click", function() {
            var win = window.open("", "OpenID Connect login",
                                  "width=500, height=500, menubar=no, location=yes, toolbar=no, status=yes");
            win.document.head.innerHTML = "<title>" + i18n.translate("openid-title") + "</title>"
                + "<link rel=\"stylesheet\" type=\"text/css\" href=\"" + api.endpoint + "/css/isso.css\">";
            win.document.body.setAttribute("class", "isso-openid-popup");
            win.document.body.innerHTML = jade.render("openid-identifier", {});
            win.document.getElementById("isso-openid-logo").setAttribute("src", api.endpoint + "/images/openid-icon-64x64.png");
            win.document.getElementById("isso-openid-login-form").setAttribute("action", api.endpoint + "/openid/login");
        });
    }

    var isLoggedIn = function() {
        return loggedIn;
    }

    var getAuthorData = function() {
        return {
            network: "openid",
            id: sessionID,
            idToken: null,
            pictureURL: authorData.pictureURL,
            name: authorData.name,
            email: authorData.email,
            website: authorData.website,
        };
    }

    var prepareComment = function(comment) {
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
