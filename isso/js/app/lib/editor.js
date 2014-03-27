define(["app/dom", "app/markup"], function($, Mark) {
    "use strict";

    return function(el) {
        el.setAttribute("contentEditable", true);

        el.on("focus", function() {
            if (el.classList.contains("placeholder")) {
                el.innerHTML = "";
                el.classList.remove("placeholder");
            }
        });

        el.on("blur", function() {
            if (el.textContent.length === 0) {
                el.textContent = Mark.up("{{ i18n-postbox-text }}");
                el.classList.add("placeholder");
            }
        });

        return el;
    };

});