define(["q"], function(Q) {

    "use strict";

    // JS Identicon generation via Gregory Schier (http://codepen.io/gschier/pen/GLvAy)
    // extended to produce the same identicon for a given hash

    // Size of a grid square in pixels
    var SQUARE = 8;

    // Number of squares width and height
    var GRID = 5;

    // Padding on the edge of the canvas in px

    var pad = function(n, width) {
        return n.length >= width ? n : new Array(width - n.length + 1).join("0") + n;
    };

    /**
     * Fill in a square on the canvas.
     */
    var fill = function(svg, x, y, padding, size, color) {
        var rect = document.createElementNS("http://www.w3.org/2000/svg", "rect");

        rect.setAttribute("x", padding + x * size);
        rect.setAttribute("y", padding + y * size);
        rect.setAttribute("width", size);
        rect.setAttribute("height", size);
        rect.setAttribute("style", "fill: " + color);

        svg.appendChild(rect);
    };

    /**
     * Pick random squares to fill in.
     */
    var generateIdenticon = function(key, padding, size) {

        var svg =  document.createElementNS("http://www.w3.org/2000/svg", "svg");
        svg.setAttribute("version", "1.1");
        svg.setAttribute("viewBox", "0 0 " + size + " " + size);
        svg.setAttribute("preserveAspectRatio", "xMinYMin meet");
        svg.setAttribute("shape-rendering", "crispEdges");
        fill(svg, 0, 0, 0, size + 2*padding, "#F0F0F0");

        if (typeof key === null) {
            return svg;
        }

        Q.when(key, function(key) {
            var hash = pad((parseInt(key, 16) % Math.pow(2, 18)).toString(2), 18),
                index = 0, color = null;

            svg.setAttribute("data-hash", key);

            // via http://colrd.com/palette/19308/
            switch (hash.substring(hash.length - 3, hash.length)) {
            case "000":
                color = "#9abf88";
                break;
            case "001":
                color = "#5698c4";
                break;
            case "010":
                color = "#e279a3";
                break;
            case "011":
                color = "#9163b6";
                break;
            case "100":
                color = "#be5168";
                break;
            case "101":
                color = "#f19670";
                break;
            case "110":
                color = "#e4bf80";
                break;
            case "111":
                color = "#447c69";
                break;
            }

            // FILL THE SQUARES
            for (var x=0; x<Math.ceil(GRID/2); x++) {
                for (var y=0; y<GRID; y++) {

                    if (hash.charAt(index) === "1") {
                        fill(svg, x, y, padding, 8, color);

                        // FILL RIGHT SIDE SYMMETRICALLY
                        if (x < Math.floor(GRID/2)) {
                            fill(svg, (GRID-1) - x, y, padding, 8, color);
                        }
                    }
                    index++;
                }
            }
        });

        return svg;
    };

    var generateBlank = function(height, width) {

        var blank = parseInt([
            0, 1, 1, 1, 1,
            1, 0, 1, 1, 0,
            1, 1, 1, 1, 1, /* purple: */ 0, 1, 0
        ].join(""), 2).toString(16);

        var el = generateIdenticon(blank, height, width);
        el.classList.add("blank");

        return el;
    };

    return {
        generate: generateIdenticon,
        blank: generateBlank
    };
});