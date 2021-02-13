# INSTALLATION:
# pip install sphinx
# npm install -g requirejs uglify-js jade
# apt install sassc

ISSO_JS_SRC := $(shell find isso/js/app -type f) \
	       $(shell ls isso/js/*.js | grep -vE "(min|dev)") \
	       isso/js/lib/requirejs-jade/jade.js

ISSO_JS_DST := isso/js/embed.min.js isso/js/embed.dev.js \
	       isso/js/count.min.js isso/js/count.dev.js

ISSO_CSS := isso/css/isso.css

ISSO_PY_SRC := $(shell git ls-files | grep -E "^isso/.+.py$$")

DOCS_RST_SRC := $(shell find docs/ -type f -name '*.rst') \
		$(wildcard docs/_isso/*) \
	        docs/index.html docs/conf.py docs/docutils.conf \
		share/isso.conf

DOCS_CSS_SRC := docs/_static/css/site.scss

DOCS_CSS_DEP := $(shell find docs/_static/css/neat -type f) \
		$(shell find docs/_static/css/bourbon -type f)

DOCS_CSS_DST := docs/_static/css/site.css

DOCS_MAN_DST := man/man1/isso.1 man/man5/isso.conf.5

DOCS_HTML_DST := docs/_build/html

RJS = npx --no-install r.js

SASS = sassc

all: man js site

init:
	npm install

flakes:
	flake8 . --count --max-line-length=127 --show-source --statistics

isso/js/%.min.js: $(ISSO_JS_SRC) $(ISSO_CSS)
	$(RJS) -o isso/js/build.$*.js out=$@

isso/js/%.dev.js: $(ISSO_JS_SRC) $(ISSO_CSS)
	$(RJS) -o isso/js/build.$*.js optimize="none" out=$@

js: $(ISSO_JS_DST)

man: $(DOCS_RST_SRC)
	sphinx-build -b man docs/ man/
	mkdir -p man/man1/ man/man5
	mv man/isso.1 man/man1/isso.1
	mv man/isso.conf.5 man/man5/isso.conf.5

${DOCS_CSS_DST}: $(DOCS_CSS_SRC) $(DOCS_CSS_DEP)
	$(SASS) $(DOCS_CSS_SRC) $@

${DOCS_HTML_DST}: $(DOCS_RST_SRC) $(DOCS_CSS_DST)
	sphinx-build -b dirhtml docs/ $@

site: $(DOCS_HTML_DST)

coverage: $(ISSO_PY_SRC)
	nosetests --with-doctest --with-coverage --cover-package=isso --cover-html isso/

test: $($ISSO_PY_SRC)
	python3 setup.py nosetests

clean:
	rm -f $(DOCS_MAN_DST) $(DOCS_CSS_DST) $(ISSO_JS_DST)
	rm -rf $(DOCS_HTML_DST)

.PHONY: clean site man init js coverage test

