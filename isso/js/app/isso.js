/* Isso – Ich schrei sonst!
*/
var $ = require("app/dom");
var utils = require("app/utils");
var config = require("app/config");
var api = require("app/api");
var template = require("app/template");
var i18n = require("app/i18n");
var identicons = require("app/lib/identicons");
var globals = require("app/globals");

"use strict";

var Postbox = function(parent) {

    var localStorage = utils.localStorageImpl,
        el = $.htmlify(template.render("postbox", {
        "author":  JSON.parse(localStorage.getItem("isso-author")),
        "email":   JSON.parse(localStorage.getItem("isso-email")),
        "website": JSON.parse(localStorage.getItem("isso-website")),
        "preview": ''
    }));

    // callback on success (e.g. to toggle the reply button)
    el.onsuccess = function() {};

    el.validate = function() {
        if ($(".isso-textarea", this).value.length < 3) {
            $(".isso-textarea", this).focus();
            return false;
        }
        if (config["require-email"] &&
            $("[name='email']", this).value.length <= 0)
        {
          $("[name='email']", this).focus();
          return false;
        }
        if (config["require-author"] &&
            $("[name='author']", this).value.length <= 0)
        {
          $("[name='author']", this).focus();
          return false;
        }
        return true;
    };

    // only display notification checkbox if email is filled in
    var email_edit = function() {
        if (config["reply-notifications"] && $("[name='email']", el).value.length > 0) {
            $(".isso-notification-section", el).show();
        } else {
            $(".isso-notification-section", el).hide();
        }
    };
    $("[name='email']", el).on("input", email_edit);
    email_edit();

    // email is not optional if this config parameter is set
    if (config["require-email"]) {
        $("[for='isso-postbox-email']", el).textContent =
            $("[for='isso-postbox-email']", el).textContent.replace(/ \(.*\)/, "");
    }

    // author is not optional if this config parameter is set
    if (config["require-author"]) {
      $("[for='isso-postbox-author']", el).textContent =
        $("[for='isso-postbox-author']", el).textContent.replace(/ \(.*\)/, "");
    }

    // preview function
    $("[name='preview']", el).on("click", function() {
        api.preview($(".isso-textarea", el).value).then(
            function(html) {
                $(".isso-preview .isso-text", el).innerHTML = html;
                el.classList.add('isso-preview-mode');
            });
    });

    // edit function
    var edit = function() {
        $(".isso-preview .isso-text", el).innerHTML = '';
        el.classList.remove('isso-preview-mode');
    };
    $("[name='edit']", el).on("click", function() {
      edit();
      $(".isso-textarea", el).focus();
    });
    $(".isso-preview", el).on("click", function() {
      edit();
      $(".isso-textarea", el).focus();
    });

    // submit form, initialize optional fields with `null` and reset form.
    // If replied to a comment, remove form completely.
    $("[type=submit]", el).on("click", function() {
        edit();
        if (! el.validate()) {
            return;
        }

        var author = $("[name=author]", el).value || null,
            email = $("[name=email]", el).value || null,
            website = $("[name=website]", el).value || null;

        localStorage.setItem("isso-author", JSON.stringify(author));
        localStorage.setItem("isso-email", JSON.stringify(email));
        localStorage.setItem("isso-website", JSON.stringify(website));

        api.create($("#isso-thread").getAttribute("data-isso-id"), {
            author: author, email: email, website: website,
            text: $(".isso-textarea", el).value,
            parent: parent || null,
            title: $("#isso-thread").getAttribute("data-title") || null,
            notification: $("[name=notification]", el).checked() ? 1 : 0,
        }).then(function(comment) {
            $(".isso-textarea", el).value = "";
            insert({ comment, scrollIntoView: true, offset: 0 });

            if (parent !== null) {
                el.onsuccess();
            }
        });
    });

    return el;
};

var insert_loader = function(comment, offset) {
    var entrypoint;
    if (comment.id === null) {
        entrypoint = $("#isso-root");
        comment.name = 'null';
    } else {
        entrypoint = $("#isso-" + comment.id + " > .isso-follow-up");
        comment.name = comment.id;
    }
    var el = $.htmlify(template.render("comment-loader", {"comment": comment}));

    entrypoint.append(el);

    $("a.isso-load-hidden", el).on("click", function() {
        el.remove();

        api.fetch({
            tid: $("#isso-thread").getAttribute("data-isso-id"),
            limit: config["reveal-on-click"],
            nested_limit: config["max-comments-nested"],
            parent: comment.id,
            sort: config["sorting"],
            offset: offset
        }).then(
            function(rv) {
                if (rv.total_replies === 0) {
                    return;
                }

                rv.replies.forEach(function(commentObject) {
                    insert({ comment: commentObject, scrollIntoView: false, offset: 0 });

                });

                if(rv.hidden_replies > 0) {
                    insert_loader(rv, offset + rv.replies.length);
                }
            },
            function(err) {
                console.log(err);
            }
        );
    });
};

var insert = function({ comment, scrollIntoView, offset }) {
    var el = $.htmlify(template.render("comment", {"comment": comment}));

    // update datetime every 60 seconds
    var refresh = function() {
        $(".isso-permalink > time", el).textContent = i18n.ago(
            globals.offset.localTime(), new Date(parseInt(comment.created, 10) * 1000));
        setTimeout(refresh, 60*1000);
    };

    // run once to activate
    refresh();

    if (config["avatar"]) {
        $(".isso-avatar > svg", el).replace(identicons.generate(comment.hash, 4, 48, config));
    }

    var entrypoint;
    if (comment.parent === null) {
        entrypoint = $("#isso-root");
    } else {
        entrypoint = $("#isso-" + comment.parent + " > .isso-follow-up");
    }

    entrypoint.append(el);

    if (scrollIntoView) {
        el.scrollIntoView();
    }

    var footer = $("#isso-" + comment.id + " > .isso-text-wrapper > .isso-comment-footer"),
        header = $("#isso-" + comment.id + " > .isso-text-wrapper > .isso-comment-header"),
        text   = $("#isso-" + comment.id + " > .isso-text-wrapper > .isso-text");

    var form = null;  // XXX: probably a good place for a closure
    $("a.isso-reply", footer).toggle("click",
        function(toggler) {
            form = footer.insertAfter(new Postbox(comment.parent === null ? comment.id : comment.parent));
            form.onsuccess = function() { toggler.next(); };
            $(".isso-textarea", form).focus();
            $("a.isso-reply", footer).textContent = i18n.translate("comment-close");
        },
        function() {
            form.remove();
            $("a.isso-reply", footer).textContent = i18n.translate("comment-reply");
        }
    );

    if (config.vote) {
        var voteLevels = config['vote-levels'];
        if (typeof voteLevels === 'string') {
            // Eg. -5,5,15
            voteLevels = voteLevels.split(',');
        }

        // update vote counter
        var votes = function (value) {
            var span = $("span.isso-votes", footer);
            if (span === null) {
                footer.prepend($.new("span.isso-votes", value));
            } else {
                span.textContent = value;
            }
            if (value) {
                el.classList.remove('isso-no-votes');
            } else {
                el.classList.add('isso-no-votes');
            }
            if (voteLevels) {
                var before = true;
                for (var index = 0; index <= voteLevels.length; index++) {
                    if (before && (index >= voteLevels.length || value < voteLevels[index])) {
                        el.classList.add('isso-vote-level-' + index);
                        before = false;
                    } else {
                        el.classList.remove('isso-vote-level-' + index);
                    }
                }
            }
        };

        $("a.isso-upvote", footer).on("click", function () {
            api.like(comment.id).then(function (rv) {
                votes(rv.likes - rv.dislikes);
            });
        });

        $("a.isso-downvote", footer).on("click", function () {
            api.dislike(comment.id).then(function (rv) {
                votes(rv.likes - rv.dislikes);
            });
        });

        votes(comment.likes - comment.dislikes);
    }

    $("a.isso-edit", footer).toggle("click",
        function(toggler) {
            var edit = $("a.isso-edit", footer);
            var avatar = config["avatar"] || config["gravatar"] ? $(".isso-avatar", el, false)[0] : null;

            edit.textContent = i18n.translate("comment-save");
            edit.insertAfter($.new("a.isso-cancel", i18n.translate("comment-cancel"))).on("click", function() {
                toggler.canceled = true;
                toggler.next();
            });

            toggler.canceled = false;
            api.view(comment.id, 1).then(function(rv) {
                var textarea = $.new("textarea.isso-textarea");
                textarea.setAttribute("rows", 5);
                textarea.setAttribute("minlength", 3);
                textarea.setAttribute("maxlength", 65535);

                textarea.value = rv.text;
                textarea.focus();

                text.classList.remove("isso-text");
                text.classList.add("isso-textarea-wrapper");

                text.textContent = "";
                text.append(textarea);
            });

            if (avatar !== null) {
                avatar.hide();
            }
        },
        function(toggler) {
            var textarea = $(".isso-textarea", text);
            var avatar = config["avatar"] || config["gravatar"] ? $(".isso-avatar", el, false)[0] : null;

            if (! toggler.canceled && textarea !== null) {
                if (textarea.value.length < 3) {
                    textarea.focus();
                    toggler.wait();
                    return;
                } else {
                    api.modify(comment.id, {"text": textarea.value}).then(function(rv) {
                        text.innerHTML = rv.text;
                        comment.text = rv.text;
                    });
                }
            } else {
                text.innerHTML = comment.text;
            }

            text.classList.remove("isso-textarea-wrapper");
            text.classList.add("isso-text");

            if (avatar !== null) {
                avatar.show();
            }

            $("a.isso-cancel", footer).remove();
            $("a.isso-edit", footer).textContent = i18n.translate("comment-edit");
        }
    );

    $("a.isso-delete", footer).toggle("click",
        function(toggler) {
            var del = $("a.isso-delete", footer);
            var state = ! toggler.state;

            del.textContent = i18n.translate("comment-confirm");
            del.on("mouseout", function() {
                del.textContent = i18n.translate("comment-delete");
                toggler.state = state;
                del.onmouseout = null;
            });
        },
        function() {
            var del = $("a.isso-delete", footer);
            api.remove(comment.id).then(function(rv) {
                if (rv) {
                    el.remove();
                } else {
                    $("span.isso-note", header).textContent = i18n.translate("comment-deleted");
                    text.innerHTML = "<p>&nbsp;</p>";
                    $("a.isso-edit", footer).remove();
                    $("a.isso-delete", footer).remove();
                }
                del.textContent = i18n.translate("comment-delete");
            });
        }
    );

    // remove edit and delete buttons when cookie is gone
    var clear = function(button) {
        if (! utils.cookie("isso-" + comment.id)) {
            if ($(button, footer) !== null) {
                $(button, footer).remove();
            }
        } else {
            setTimeout(function() { clear(button); }, 15*1000);
        }
    };

    clear("a.isso-edit");
    clear("a.isso-delete");

    // show direct reply to own comment when cookie is max aged
    var show = function(el) {
        if (utils.cookie("isso-" + comment.id)) {
            setTimeout(function() { show(el); }, 15*1000);
        } else {
            footer.append(el);
        }
    };

    if (! config["reply-to-self"] && utils.cookie("isso-" + comment.id)) {
        show($("a.isso-reply", footer).detach());
    }

    if (comment.hasOwnProperty('replies')) {
        comment.replies.forEach(function (replyObject) {
            insert({ comment: replyObject, scrollIntoView: false, offset: offset + 1 });
        });
        if (comment.hidden_replies > 0) {
            insert_loader(comment, offset + comment.replies.length);
        }
    }

};

module.exports = {
    insert: insert,
    insert_loader: insert_loader,
    Postbox: Postbox,
};
