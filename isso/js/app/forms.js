define(["lib/HTML"], function(HTML) {

    var msgbox = function(defaults) {

        var form = document.createElement("div")
        form.className = "isso-comment-box"
        HTML.ify(form);

        var optional = form.add("ul.optional");
        optional.add("li>input[type=text name=author placeholder=Name ]").value = defaults.author || "";
        optional.add("li>input[type=email name=email placeholder=Email]").value = defaults.email || "";
        optional.add("li>input[type=url name=website placeholder=Website]").value = defaults.website || "";

        var textarea = form.add("div>textarea[rows=2 name=text]");
        textarea.value = defaults.text || "";
        textarea.placeholder = "Kommentar hier eintippen (andere Felder sind optional)"
        textarea.onfocus = function() {
            textarea.rows = 8;
            // scrollIntoView enhancement
        };

        form.add("input[type=submit]").value = "Kommentar hinzufügen";
        form.add("span");
        return form;

    }

    var validate = function(msgbox) {
        if (msgbox.query("textarea").value.length < 3) {
            msgbox.query("textarea").focus();
            msgbox.span.className = "isso-popup"
            msgbox.span.innerHTML = "Dein Kommentar sollte schon etwas länger sein.";
            msgbox.span.addEventListener("click", function(event) {
                msgbox.span.className = "";
                msgbox.span.innerHTML = "";
            })
            setTimeout(function() {
                msgbox.span.className = ""
                msgbox.span.innerHTML = ""
            }, 5000 )
            return false;
        }

        return true;
    }

    return {
        msgbox: msgbox,
        validate: validate
    }
});