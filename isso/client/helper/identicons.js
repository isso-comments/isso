define(function() {

    // JS Identicon generation via Gregory Schier (http://codepen.io/gschier/pen/GLvAy)
    // modified to work with a given seed using Jenkins hashing.

    // Size of a grid square in pixels
    var SQUARE = 8;

    // Number of squares width and height
    var GRID = 5;

    // Padding on the edge of the canvas in px
    var PADDING = SQUARE/2;

    /* Jenkins 18-bit hash */
    var jenkins = function(key) {
        var hash = 0;

        for (var i=0; i<key.length; ++i) {
            hash += key.charCodeAt(i);
            hash += (hash << 10);
            hash ^= (hash >> 6);
        }

        hash += (hash << 3);
        hash ^= (hash >> 11);
        hash += (hash << 15);

        return (hash >>> 0) % Math.pow(2, 18);
    }

    var pad = function(n, width) {
        return n.length >= width ? n : new Array(width - n.length + 1).join("0") + n;
    }

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
    var generateIdenticon = function(ctx, key) {

        var hash = pad(jenkins(key).toString(2), 18),
            index = 0, color = null;

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

        // FILL CANVAS BG
        ctx.beginPath();
        ctx.rect(0, 0, 48, 48);
        ctx.fillStyle = '#F0F0F0';
        ctx.fill();

        // FILL THE SQUARES
        for (var x=0; x<Math.ceil(GRID/2); x++) {
            for (var y=0; y<GRID; y++) {

                if (hash.charAt(index) == "1") {
                    fillBlock(x, y, color, ctx);

                    // FILL RIGHT SIDE SYMMETRICALLY
                    if (x < Math.floor(GRID/2)) {
                        fillBlock((GRID-1) - x, y, color, ctx);
                    }
                }
            index++;
            }
        }

        return ctx;
    };

    return {
        generate: generateIdenticon,
        hash: jenkins
    };
})