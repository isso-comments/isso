ISSO_SRC := $(shell find isso/js/app -type f) $(shell ls isso/js/*.js | grep -vE "(min|dev)")
ISSO_DST :=  isso/js/embed.min.js isso/js/embed.dev.js isso/js/count.min.js isso/js/count.dev.js

RST := $(shell find docs/ -type f -name  '*.rst')
MAN := man/man1/isso.1 man/man5/isso.conf.5

WWW := docs/index.html docs/isso.example.cfg $(wildcard docs/_static/*)
CSS := docs/_static/css/site.css

all: man js site

init:
	(cd isso/js; bower install almond requirejs requirejs-text)

isso/js/%.min.js: $(ISSO_SRC)
	r.js -o isso/js/build.$*.js out=$@

isso/js/%.dev.js: $(ISSO_SRC)
	r.js -o isso/js/build.$*.js optimize="none" out=$@

js: $(ISSO_DST)

man: $(RST)
	sphinx-build -b man docs/ man/

${CSS}: docs/_static/css/site.scss
	scss --no-cache $< $@

site: $(RST) $(WWW) $(CSS)
	cd docs && sphinx-build -b dirhtml . _build/html

coverage:
	nosetests --with-doctest --with-doctest-ignore-unicode --with-coverage \
	          --cover-package=isso --cover-html isso/ specs/

clean:
	rm -f $(MAN) $(CSS) $(ISSO_DST)

.PHONY: clean site man init js

