all: css js

css:
	scss --no-cache isso/css/isso.scss isso/css/isso.css

js:
	r.js -o isso/js/build.embed.js
	r.js -o isso/js/build.embed.js optimize="none" out="isso/js/embed.dev.js"
	r.js -o isso/js/build.count.js
	r.js -o isso/js/build.count.js optimize="none" out="isso/js/count.dev.js"
