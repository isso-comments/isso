/* Isso – Ich schrei sonst!
 */
define(["app/text/html", "app/dom", "app/utils", "app/config", "app/api", "app/markup", "app/i18n", "app/lib", "app/globals"],
    function(templates, $, utils, config, api, Mark, i18n, lib, globals) {

    "use strict";

    var msgs = i18n[i18n.lang];

    var Postbox = function(parent) {

        var el = $.htmlify(Mark.up(templates["postbox"]));

        // add a default identicon to not waste CPU cycles
        $(".avatar > svg", el).replace(lib.identicons.blank(4, 48));

        // on text area focus, generate identicon from IP address
        $(".textarea-wrapper > .textarea", el).on("focus", function() {
            if ($(".avatar svg", el).getAttribute("className") === "blank") {
                $(".avatar svg", el).replace(
                    lib.identicons.generate(lib.pbkdf2(api.remote_addr(), api.salt, 1000, 6), 4, 48));
            }
        });

        // update identicon on email input. Listens on keyup, after 200ms the
        // new identicon is generated.
        var active;
        $(".input-wrapper > [type=email]", el).on("keyup", function() {
            if (active) {
                clearTimeout(active);
            }
            active = setTimeout(function() {
                lib.pbkdf2($(".input-wrapper > [type=email]", el).value || api.remote_addr(), api.salt, 1000, 6)
                .then(function(rv) {
                    $(".avatar svg", el).replace(lib.identicons.generate(rv, 4, 48));
                });
            }, 200);
        }, false);

        $(".input-wrapper > [type=email]", el).on("keydown", function() {
            clearTimeout(active);
        }, false);

        // callback on success (e.g. to toggle the reply button)
        el.onsuccess = function() {};

        el.validate = function() {
            if (utils.text($(".textarea", this).innerHTML).length < 3 ||
                $(".textarea", this).classList.contains("placeholder"))
            {
                $(".textarea", this).focus();
                return false;
            }
            return true;
        };

        // submit form, initialize optional fields with `null` and reset form.
        // If replied to a comment, remove form completely.
        $("[type=submit]", el).on("click", function() {
            if (! el.validate()) {
                return;
            }

            api.create($("#isso-thread").getAttribute("data-isso-id"), {
                author: $("[name=author]", el).value || null,
                email: $("[name=email]", el).value || null,
                text: utils.text($(".textarea", el).innerHTML),
                parent: parent || null
            }).then(function(comment) {
                $("[name=author]", el).value = "";
                $("[name=email]", el).value = "";
                $(".textarea", el).innerHTML = "";
                $(".textarea", el).blur();
                insert(comment, true);

                if (parent !== null) {
                    el.onsuccess();
                }
            });
        });

        lib.editorify($(".textarea", el));

        return el;
    };

    var insert_loader = function(commentWrapper, lastcreated) {
        var entrypoint;
        if (commentWrapper.id === null) {
            entrypoint = $("#isso-root");
            commentWrapper.name = 'null';
        } else {
            entrypoint = $("#isso-" + commentWrapper.id + " > .text-wrapper > .isso-follow-up");
            commentWrapper.name = commentWrapper.id;
        }
        var el = $.htmlify(Mark.up(templates["comment_loader"], commentWrapper));

        entrypoint.append(el);

        $("a.load_hidden", el).toggle("click",
            function() {
                el.remove();
                api.fetch($("#isso-thread").getAttribute("data-isso-id"),
                    config["reveal-on-click"], "0",
                    commentWrapper.id,
                    lastcreated).then(
                    function(rv) {
                        if (rv.total_replies === 0) {
                            return;
                        }

                        var lastcreated = 0;
                        rv.replies.forEach(function(commentObject) {
                            insert(commentObject, false);
                            if(commentObject.created > lastcreated) {
                                lastcreated = commentObject.created;
                            }
                        });

                        if(rv.hidden_replies > 0) {
                            insert_loader(rv, lastcreated);
                        }

                        if (window.location.hash.length > 0) {
                            $(window.location.hash).scrollIntoView();
                        }
                    },
                    function(err) {
                        console.log(err);
                    });
            });
    };

    var insert = function(comment, scrollIntoView) {
        var el = $.htmlify(Mark.up(templates["comment"], comment));

        // update datetime every 60 seconds
        var refresh = function() {
            $(".permalink > date", el).textContent = utils.ago(
                globals.offset.localTime(), new Date(parseInt(comment.created, 10) * 1000));
            setTimeout(refresh, 60*1000);
        };

        // run once to activate
        refresh();

        $("div.avatar > svg", el).replace(lib.identicons.generate(comment.hash, 4, 48));

        var entrypoint;
        if (comment.parent === null) {
            entrypoint = $("#isso-root");
        } else {
            entrypoint = $("#isso-" + comment.parent + " > .text-wrapper > .isso-follow-up");
        }

        entrypoint.append(el);

        if (scrollIntoView) {
            el.scrollIntoView();
        }

        var footer = $("#isso-" + comment.id + " > .text-wrapper > .isso-comment-footer"),
            header = $("#isso-" + comment.id + " > .text-wrapper > .isso-comment-header"),
            text   = $("#isso-" + comment.id + " > .text-wrapper > .text");

        var form = null;  // XXX: probably a good place for a closure
        $("a.reply", footer).toggle("click",
            function(toggler) {
                form = footer.insertAfter(new Postbox(comment.parent === null ? comment.id : comment.parent));
                form.onsuccess = function() { toggler.next(); };
                $(".textarea", form).focus();
                $("a.reply", footer).textContent = msgs["comment-close"];
            },
            function() {
                form.remove();
                $("a.reply", footer).textContent = msgs["comment-reply"];
            }
        );

        // update vote counter, but hide if votes sum to 0
        var votes = function(value) {
            var span = $("span.votes", footer);
            if (span === null && value !== 0) {
                footer.prepend($.new("span.votes", value));
            } else {
                if (value === 0) {
                    span.remove();
                } else {
                    span.textContent = value;
                }
            }
        };

        $("a.upvote", footer).on("click", function() {
            api.like(comment.id).then(function(rv) {
                votes(rv.likes - rv.dislikes);
            });
        });

        $("a.downvote", footer).on("click", function() {
            api.dislike(comment.id).then(function(rv) {
                votes(rv.likes - rv.dislikes);
            });
        });

        $("a.edit", footer).toggle("click",
            function(toggler) {
                var edit = $("a.edit", footer);

                edit.textContent = msgs["comment-save"];
                edit.insertAfter($.new("a.cancel", msgs["comment-cancel"])).on("click", function() {
                    toggler.canceled = true;
                    toggler.next();
                });

                toggler.canceled = false;
                api.view(comment.id, 1).then(function(rv) {
                    var textarea = lib.editorify($.new("div.textarea"));

                    textarea.innerHTML = utils.detext(rv.text);
                    textarea.focus();

                    text.classList.remove("text");
                    text.classList.add("textarea-wrapper");

                    text.textContent = "";
                    text.append(textarea);
                });
            },
            function(toggler) {
                var textarea = $(".textarea", text);

                if (! toggler.canceled && textarea !== null) {
                    if (utils.text(textarea.innerHTML).length < 3) {
                        textarea.focus();
                        toggler.wait();
                        return;
                    } else {
                        api.modify(comment.id, {"text": utils.text(textarea.innerHTML)}).then(function(rv) {
                            text.innerHTML = rv.text;
                            comment.text = rv.text;
                        });
                    }
                } else {
                    text.innerHTML = comment.text;
                }

                text.classList.remove("textarea-wrapper");
                text.classList.add("text");

                $("a.cancel", footer).remove();
                $("a.edit", footer).textContent = msgs["comment-edit"];
            }
        );

        $("a.delete", footer).toggle("click",
            function(toggler) {
                var del = $("a.delete", footer);
                var state = ! toggler.state;

                del.textContent = msgs["comment-confirm"];
                del.on("mouseout", function() {
                    del.textContent = msgs["comment-delete"];
                    toggler.state = state;
                    del.onmouseout = null;
                });
            },
            function() {
                var del = $("a.delete", footer);
                api.remove(comment.id).then(function(rv) {
                    if (rv) {
                        el.remove();
                    } else {
                        $("span.note", header).textContent = msgs["comment-deleted"];
                        text.innerHTML = "<p>&nbsp;</p>";
                        $("a.edit", footer).remove();
                        $("a.delete", footer).remove();
                    }
                    del.textContent = msgs["comment-delete"];
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

        clear("a.edit");
        clear("a.delete");

        // show direct reply to own comment when cookie is max aged
        var show = function(el) {
            if (utils.cookie("isso-" + comment.id)) {
                setTimeout(function() { show(el); }, 15*1000);
            } else {
                footer.append(el);
            }
        };

        if (! config["reply-to-self"] && utils.cookie("isso-" + comment.id)) {
            show($("a.reply", footer).detach());
        }

        if(comment.hasOwnProperty('replies')) {
            var lastcreated = 0;
            comment.replies.forEach(function(replyObject) {
                insert(replyObject, false);
                if(replyObject.created > lastcreated) {
                    lastcreated = replyObject.created;
                }

            });
            if(comment.hidden_replies > 0) {
                insert_loader(comment, lastcreated);
            }

        }

    };

    return {
        insert: insert,
        insert_loader: insert_loader,
        Postbox: Postbox
    };
});
