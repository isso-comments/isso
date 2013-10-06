define(function() {

    "use strict";

    window.Element.prototype.replace = function(el) {
        var element = DOM.htmlify(el);
        this.parentNode.replaceChild(element, this);
        return element;
    };

    window.Element.prototype.prepend = function(el) {
        var element = DOM.htmlify(el);
        this.insertBefore(element, this.firstChild);
        return element;
    };

    window.Element.prototype.append = function(el) {
        var element = DOM.htmlify(el);
        this.appendChild(element);
        return element;
    };

    window.Element.prototype.insertAfter = function(el) {
        var element = DOM.htmlify(el);
        this.parentNode.insertBefore(element, this.nextSibling);
        return element;
    };

    window.Element.prototype.on = function(type, listener, prevent) {
        /*
        Shortcut for `Element.addEventListener`, prevents default event
        by default, set :param prevents: to `false` to change that behavior.
         */
        this.addEventListener(type, function(event) {
            listener();
            if (prevent === undefined || prevent) {
                event.preventDefault();
            }
        });
    };

    window.Element.prototype.toggle = function(type, on, off) {
        /*
        Toggle between two internal states on event :param type: e.g. to
        cycle form visibility. Callback :param on: is called on first event,
        :param off: next time.

        You can skip to the next state without executing the callback with
        `toggler.next()`. You can prevent a cycle when you call `toggler.wait()`
        during an event.
         */

        function Toggle(el, on, off) {
            this.state = false;
            this.el = el;
            this.on = on;
            this.off = off;
        }

        Toggle.prototype.next = function next() {
            if (! this.state) {
                this.state = true;
                this.on(this);
            } else {
                this.state = false;
                this.off(this);
            }
        };

        Toggle.prototype.wait = function wait() {
            this.state = ! this.state;
        };

        var toggler = new Toggle(this, on, off);
        this.on(type, function() {
            toggler.next();
        });
    };

    window.Element.prototype.remove = function() {
        // Mimimi, I am IE and I am so retarded, mimimi.
        this.parentNode.removeChild(this);
    };

    var DOM = function(query, root) {
        /*
        jQuery-like CSS selector which returns on :param query: either a
        single node, a node list or null.

        :param root: only queries within the given element.
         */

        if (! root) {
            root = window.document;
        }

        var elements = root.querySelectorAll(query);

        if (elements.length === 0) {
            return null;
        }

        if (elements.length === 1) {
            return elements[0];
        }

        return elements;
    };

    DOM.htmlify = function(html) {
        /*
        Convert :param html: into an Element (if not already).
         */

        if (html instanceof window.Element) {
            return html;
        }

        var wrapper = DOM.new("div");
        wrapper.innerHTML = html;
        return wrapper.firstChild;
    };

    DOM.new = function(tag, content) {
        /*
        A helper to build HTML with pure JS. You can pass class names and
        default content as well:

            var par = DOM.new("p"),
                div = DOM.new("p.some.classes"),
                div = DOM.new("textarea.foo", "...")
         */

        var el = document.createElement(tag.split(".")[0]);
        tag.split(".").slice(1).forEach(function(val) { el.classList.add(val); });

        if (["A", "LINK"].indexOf(el.nodeName) > -1) {
            el.href = "#";
        }

        if (["TEXTAREA", "INPUT"].indexOf(el.nodeName) > -1) {
            el.value = content || "";
        } else {
            el.textContent = content || "";
        }
        return el;
    };

    DOM.each = function(tag, func) {
        // XXX really needed? Maybe better as NodeList method
        Array.prototype.forEach.call(document.getElementsByTagName(tag), func);
    };

    return DOM;
});