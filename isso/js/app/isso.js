/* Isso – Ich schrei sonst!
 */
define(["behave", "app/text/html", "app/dom", "app/utils", "app/api", "app/markup", "app/i18n", "app/lib"],
    function(behave, templates, $, utils, api, Mark, i18n, lib) {

    "use strict";

    var msgs = i18n[i18n.lang];

    var toggle = function(el, on, off) {
        if (el.classList.contains("off") || ! el.classList.contains("on")) {
            el.classList.remove("off");
            el.classList.add("on");
            on(el);
        } else {
            el.classList.remove("on");
            el.classList.add("off");
            off(el);
        }
    };

    var Postbox = function(parent) {

        var el = $.htmlify(Mark.up(templates["postbox"]));

        // add a blank identicon to not waste CPU cycles
        // XXX show a space invader instead :>
        $(".avatar > canvas", el).replace(lib.identicons.blank(48, 48));

        // on text area focus, generate identicon from IP address
        $(".textarea-wrapper > textarea", el).on("focus", function() {
            if ($(".avatar canvas", el).classList.contains("blank")) {
                $(".avatar canvas", el).replace(
                    lib.identicons.generate(lib.pbkdf2(api.remote_addr, api.salt, 1000, 6), 48, 48));
            }
        });

        // update identicon, when the user provices an email address
        var active;
        $(".input-wrapper > [type=email]", el).on("keyup", function() {
            if (active) {
                clearTimeout(active);
            }
            active = setTimeout(function() {
                lib.pbkdf2($(".input-wrapper > [type=email]", el).value || api.remote_addr, api.salt, 1000, 6)
                .then(function(rv) {
                    $(".avatar canvas", el).replace(lib.identicons.generate(rv, 48, 48));
                });
            }, 200);
        }, false);

        $(".input-wrapper > [type=email]", el).on("keydown", function() {
            clearTimeout(active);
        }, false);

        el.validate = function() {
            if ($("textarea", this).value.length < 3) {
                $("textarea", this).focus();
                return false;
            }
            return true;
        };

        $("[type=submit]", el).on("click", function() {
            if (! el.validate()) {
                return;
            }

            api.create({
                author: $("[name=author]", el).value || null,
                email: $("[name=email]", el).value || null,
                text: $("textarea", el).value,
                parent: parent || null
            }).then(function(comment) {
                $("[name=author]", el).value = "";
                $("[name=email]", el).value = "";
                $("textarea", el).value = "";
                $("textarea", el).rows = 2;
                $("textarea", el).blur();
                insert(comment, true);

                if (parent !== null) {
                    el.remove();
                }
            });
        });

        var editor = new behave({textarea: $("textarea", el)});

        return el;
    };

    var map  = {id: {}, name: {}};

    var insert = function(comment, scrollIntoView) {

        map.name[comment.id] = comment.author;
        if (comment.parent) {
            comment["replyto"] = map.name[comment.parent];
        }

        var el = $.htmlify(Mark.up(templates["comment"], comment));

        var refresh = function() {
            $(".permalink > date", el).textContent = utils.ago(new Date(parseInt(comment.created, 10) * 1000));
            setTimeout(refresh, 60*1000);
        };  refresh();

        $("div.avatar > canvas", el).replace(lib.identicons.generate(comment.hash, 48, 48));

        var entrypoint;
        if (comment.parent === null) {
            entrypoint = $("#isso-root");
        } else {
            var key = comment.parent;
            while (key in map.id) {
                key = map.id[key];
            }
            map.id[comment.id] = comment.parent;
            entrypoint = $("#isso-" + key + " > .text-wrapper > .isso-follow-up");
        }

        entrypoint.append(el);

        if (scrollIntoView) {
            el.scrollIntoView();
        }

        var footer = $("#isso-" + comment.id + " > .text-wrapper > footer"),
            header = $("#isso-" + comment.id + " > .text-wrapper > header");

        var form = new Postbox(comment.id);
        $("a.reply", footer).on("click", function() {
            toggle(
                $("a.reply", footer),
                function(reply) {
                    footer.insertAfter(form);
                    reply.textContent = msgs["comment-close"];
                },
                function(reply) {
                    form.remove();
                    reply.textContent = msgs["comment-reply"];
                }
            );
        });

        if (comment.parent !== null) {
            $("a.parent", header).on("mouseover", function() {
                $("#isso-" + comment.parent).classList.add("parent-highlight");
            });
            $("a.parent", header).on("mouseout", function() {
                $("#isso-" + comment.parent).classList.remove("parent-highlight");
            });
        }

        var votes = function (value) {
            var span = $("span.votes", footer);
            if (span === null) {
                if (value === 0) {
                    span.remove();
                    return;
                } else {
                    footer.prepend($.htmlify('<span class="votes">' + value + '</span>'));
                }
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

        if (! utils.cookie(comment.id)) {
//            $("a.edit", footer).remove();
            $("a.delete", footer).remove();
            return;
        }

        $("a.delete", footer).on("click", function() {
            if ($("a.delete", footer).textContent === msgs["comment-confirm"]) {
                api.remove(comment.id).then(function(rv) {
                    if (rv) {
                        el.remove();
                    } else {
                        $("span.note", el).textContent = "Kommentar gelöscht.";
                        $(".text", el).innerHTML = "<p>&nbsp;</p>";
                    }
                });
            } else {
                $("a.delete", footer).textContent = msgs["comment-confirm"];
                setTimeout(function() {
                    $("a.delete", footer).textContent = msgs["comment-delete"];
                }, 1500);
            }
        });
    };

    return {
        insert: insert,
        Postbox: Postbox
    };
});