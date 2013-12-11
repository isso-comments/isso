all: css js

css:
	scss isso/css/isso.scss isso/css/isso.css

js:
	r.js -o isso/js/build.embed.js
	r.js -o isso/js/build.embed.js optimize="none" out="isso/js/embed.dev.js"
	r.js -o isso/js/build.count.js
	r.js -o isso/js/build.count.js optimize="none" out="isso/js/count.dev.js"
site:
	cd docs/ && sphinx-build -E -b dirhtml -a . _build
	scss docs/_static/css/site.scss docs/_build/_static/css/site.css

