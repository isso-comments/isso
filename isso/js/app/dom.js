define(function() {

    "use strict";

    function Element(node) {
        this.obj = node;

        this.replace = function (el) {
            var element = DOM.htmlify(el);
            node.parentNode.replaceChild(element.obj, node);
            return element;
        };

        this.prepend = function (el) {
            var element = DOM.htmlify(el);
            node.insertBefore(element.obj, node.firstChild);
            return element;
        };

        this.append = function (el) {
            var element = DOM.htmlify(el);
            node.appendChild(element.obj);
            return element;
        };

        this.insertAfter = function(el) {
            var element = DOM.htmlify(el);
            node.parentNode.insertBefore(element.obj, node.nextSibling);
            return element;
        };

        /**
         * Shortcut for `Element.addEventListener`, prevents default event
         * by default, set :param prevents: to `false` to change that behavior.
         */
        this.on = function(type, listener, prevent) {
            node.addEventListener(type, function(event) {
                listener(event);
                if (prevent === undefined || prevent) {
                    event.preventDefault();
                }
            });
        };

        /**
         * Toggle between two internal states on event :param type: e.g. to
         * cycle form visibility. Callback :param a: is called on first event,
         * :param b: next time.
         *
         * You can skip to the next state without executing the callback with
         * `toggler.next()`. You can prevent a cycle when you call `toggler.wait()`
         * during an event.
         */
        this.toggle = function(type, a, b) {

            var toggler = new Toggle(a, b);
            this.on(type, function() {
                toggler.next();
            });
        };

        this.detach = function() {
            // Detach an element from the DOM and return it.
            node.parentNode.removeChild(this.obj);
            return this;
        };

        this.remove = function() {
            // IE quirks
            node.parentNode.removeChild(this.obj);
        };

        this.show = function() {
            node.style.display = "block";
        };

        this.hide = function() {
            node.style.display = "none";
        };

        this.setText = function(text) {
            node.textContent = text;
        };

        this.setHtml = function(html) {
            node.innerHTML = html;
        };

        this.blur = function() { node.blur() };
        this.focus = function() { node.focus() };
        this.scrollIntoView = function(args) { node.scrollIntoView(args) };

        this.checked = function() { return node.checked; };

        this.setAttribute = function(key, value) { node.setAttribute(key, value) };
        this.getAttribute = function(key) { return node.getAttribute(key) };

        this.classList = node.classList;

        Object.defineProperties(this, {
            "textContent": {
                get: function() { return node.textContent; },
                set: function(textContent) { node.textContent = textContent; }
            },
            "innerHTML": {
                get: function() { return node.innerHTML; },
                set: function(innerHTML) { node.innerHTML = innerHTML; }
            },
            "value": {
                get: function() { return node.value; },
                set: function(value) { node.value = value; }
            },
            "placeholder": {
                get: function() { return node.placeholder; },
                set: function(placeholder) { node.placeholder = placeholder; }
            }
        });
    }

    var Toggle = function(a, b) {
        this.state = false;

        this.next = function() {
            if (! this.state) {
                this.state = true;
                a(this);
            } else {
                this.state = false;
                b(this);
            }
        };

        this.wait = function() {
            this.state = ! this.state;
        };
    };

    var DOM = function(query, root, single) {
        /*
        jQuery-like CSS selector which returns on :param query: either a
        single node (unless single=false), a node list or null.

        :param root: only queries within the given element.
         */

        if (typeof single === "undefined") {
            single = true;
        }

        if (! root) {
            root = window.document;
        }

        if (root instanceof Element) {
            root = root.obj;
        }
        var elements = [].slice.call(root.querySelectorAll(query), 0);

        if (elements.length === 0) {
            return null;
        }

        if (elements.length === 1 && single) {
            return new Element(elements[0]);
        }

        // convert NodeList to Array
        elements = [].slice.call(elements, 0);

        return elements.map(function(el) {
            return new Element(el);
        });
    };

    DOM.htmlify = function(el) {
        /*
        Convert :param html: into an Element (if not already).
        */

        if (el instanceof Element) {
            return el;
        }

        if (el instanceof window.Element) {
            return new Element(el);
        }

        var wrapper = DOM.new("div");
        wrapper.innerHTML = el;
        return new Element(wrapper.firstChild);
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

        if (!content && content !== 0) {
            content = "";
        }
        if (["TEXTAREA", "INPUT"].indexOf(el.nodeName) > -1) {
            el.value = content;
        } else {
            el.textContent = content;
        }
        return el;
    };

    DOM.each = function(tag, func) {
        // XXX really needed? Maybe better as NodeList method
        Array.prototype.forEach.call(document.getElementsByTagName(tag), func);
    };

    return DOM;
});
