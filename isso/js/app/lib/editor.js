define(["app/dom", "app/i18n"], function($, i18n) {

    "use strict";

    return function(el) {
        el = $.htmlify(el);
        el.setAttribute("contentEditable", true);

        el.on("focus", function() {
            if (el.classList.contains("placeholder")) {
                el.innerHTML = "";
                el.classList.remove("placeholder");
            }
        });

        el.on("blur", function() {
            if (el.textContent.length === 0) {
                el.textContent = i18n.translate("postbox-text");
                el.classList.add("placeholder");
            }
        });

        return el;
    };
});
