define(["q"], function(Q) {

    "use strict";

    // JS Identicon generation via Gregory Schier (http://codepen.io/gschier/pen/GLvAy)
    // extended to produce the same identicon for a given hash

    // Size of a grid square in pixels
    var SQUARE = 8;

    // Number of squares width and height
    var GRID = 5;

    // Padding on the edge of the canvas in px
    var PADDING = 4;

    var pad = function(n, width) {
        return n.length >= width ? n : new Array(width - n.length + 1).join("0") + n;
    };

    /**
     * Fill in a square on the canvas.
     */
    var fillBlock = function(x, y, color, ctx) {
        ctx.beginPath();
        ctx.rect(
            PADDING+x*SQUARE,
            PADDING+y*SQUARE,
            SQUARE,
            SQUARE
        );
        ctx.fillStyle = color;
        ctx.fill();
    };

    /**
     * Pick random squares to fill in.
     */
    var generateIdenticon = function(key, height, width) {

        var canvas = document.createElement("canvas"),
            ctx = canvas.getContext("2d");
        canvas.width = width;
        canvas.height = height;

        // FILL CANVAS BG
        ctx.beginPath();
        ctx.rect(0, 0, height, width);
        ctx.fillStyle = '#F0F0F0';
        ctx.fill();

        if (typeof key === null) {
            return canvas;
        }

        Q.when(key, function(key) {
            var hash = pad((parseInt(key, 16) % Math.pow(2, 18)).toString(2), 18),
                index = 0, color = null;

            canvas.setAttribute("data-hash", key);

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
                        fillBlock(x, y, color, ctx);

                        // FILL RIGHT SIDE SYMMETRICALLY
                        if (x < Math.floor(GRID/2)) {
                            fillBlock((GRID-1) - x, y, color, ctx);
                        }
                    }
                    index++;
                }
            }
        });

        return canvas;
    };

    var generateBlank = function(height, width) {
        var el = generateIdenticon(null, height, width);
        el.className = "blank";
        return el;
    };

    return {
        generate: generateIdenticon,
        blank: generateBlank
    };
});