# INSTALLATION:
# Docs:
#   pip install sphinx
#   apt install sassc
# Python unit tests:
#   pip install pytest pytest-cov
# Javascript frontend client:
#   make init

ISSO_JS_SRC := $(shell find isso/js/app -type f) \
	       $(shell ls isso/js/*.js | grep -vE "(min|dev)")

ISSO_JS_DST := isso/js/embed.min.js isso/js/embed.dev.js \
	       isso/js/count.min.js isso/js/count.dev.js \
	       isso/js/count.dev.js.map isso/js/embed.dev.js.map

ISSO_PY_SRC := $(shell find isso/ | grep -E '^isso/.+.py$$')

DOCS_RST_SRC := $(shell find docs/ -type f -name '*.rst') \
		$(wildcard docs/_theme/*) \
		docs/index.html docs/conf.py docs/docutils.conf \
		$(shell find docs/_extensions/)

DOCS_CSS_SRC := docs/_static/css/site.scss

DOCS_CSS_DEP := $(shell find docs/_static/css/neat -type f) \
		$(shell find docs/_static/css/bourbon -type f)

DOCS_CSS_DST := docs/_static/css/site.css

DOCS_HTML_DST := docs/_build/html

APIDOC_SRC := apidoc/apidoc.json apidoc/header.md apidoc/footer.md apidoc/_apidoc.js

APIDOC_DST := apidoc/_output

APIDOC = npx --no-install apidoc

SASS = sassc

TESTBED_IMAGE ?= isso-js-testbed:latest

all: js site

init:
	npm install --omit=optional

flakes:
	flake8 isso/ contrib/ --count --max-line-length=127 --show-source --statistics

# Note: It doesn't make sense to split up configs by output file with
# webpack, just run everything at once
isso/js/embed.min.js: $(ISSO_JS_SRC)
	npm run build-prod

isso/js/count.min.js: isso/js/embed.min.js

isso/js/embed.dev.js: $(ISSO_JS_SRC)
	npm run build-dev

isso/js/count.dev.js: isso/js/embed.dev.js

# Note: No need to depend on css sources since they are no longer inlined
js: $(ISSO_JS_DST)

css: $(DOCS_CSS_DST)

${DOCS_CSS_DST}: $(DOCS_CSS_SRC) $(DOCS_CSS_DEP)
	$(SASS) $(DOCS_CSS_SRC) $@

# Sphinx: "-W" flag turns warnings into errors, can be disabled for debugging
${DOCS_HTML_DST}: $(DOCS_RST_SRC) $(DOCS_CSS_DST)
	sphinx-build -b dirhtml -W docs/ $@

site: $(DOCS_HTML_DST)

# Generate docs using apiDoc. Config inside apidoc.json
# https://apidocjs.com/
apidoc-init:
	npm install apidoc

apidoc: $(ISSO_PY_SRC) $(APIDOC_SRC)
	$(APIDOC) --config apidoc/apidoc.json \
		--input isso/views/ --input apidoc/ \
		--output $(APIDOC_DST) --private
	cp -rT $(APIDOC_DST) $(DOCS_HTML_DST)/docs/api/

coverage: $(ISSO_PY_SRC)
	coverage run --omit='*/tests/*' --source isso -m pytest
	coverage report --omit='*/tests/*'

test: $($ISSO_PY_SRC)
	PYTHONPATH=. pytest --doctest-modules isso/

docker:
	DOCKER_BUILDKIT=1 docker build -t isso:latest .

docker-run:
	docker run -d --rm --name isso -p 127.0.0.1:8080:8080 --mount type=bind,source=$(PWD)/contrib/isso-dev.cfg,target=/config/isso.cfg,readonly isso:latest isso.run

docker-push:
	docker tag isso:latest ghcr.io/isso-comments/isso:dev
	docker push ghcr.io/isso-comments/isso:dev

docker-testbed:
	docker build -f docker/Dockerfile-js-testbed -t isso-js-testbed .

docker-testbed-push:
	docker tag isso-js-testbed:latest ghcr.io/isso-comments/isso-js-testbed:latest
	docker push ghcr.io/isso-comments/isso-js-testbed:latest

docker-js-unit:
	docker run \
		--mount type=bind,source=$(PWD)/package.json,target=/src/package.json,readonly \
		--mount type=bind,source=$(PWD)/isso/js/,target=/src/isso/js/,readonly \
		$(TESTBED_IMAGE) npm run test-unit

docker-js-integration:
	docker run \
		--mount type=bind,source=$(PWD)/package.json,target=/src/package.json,readonly \
		--mount type=bind,source=$(PWD)/isso/js/,target=/src/isso/js/ \
		--env ISSO_ENDPOINT='http://isso-dev.local:8080' \
		--network container:isso-server \
		$(TESTBED_IMAGE) npm run test-integration

docker-generate-screenshots:
	docker run \
		--mount type=bind,source=$(PWD)/package.json,target=/src/package.json,readonly \
		--mount type=bind,source=$(PWD)/isso/js/,target=/src/isso/js/ \
		--network container:isso-server \
		--env ISSO_ENDPOINT='http://isso-dev.local:8080' \
		$(TESTBED_IMAGE) npm run test-screenshots

docker-compare-screenshots: docker-generate-screenshots
	docker run \
		--mount type=bind,source=$(PWD)/package.json,target=/src/package.json,readonly \
		--mount type=bind,source=$(PWD)/isso/js/,target=/src/isso/js/ \
		$(TESTBED_IMAGE) bash isso/js/tests/screenshots/compare-hashes.sh

docker-update-screenshots: docker-generate-screenshots
	docker run \
		--mount type=bind,source=$(PWD)/package.json,target=/src/package.json,readonly \
		--mount type=bind,source=$(PWD)/isso/js/,target=/src/isso/js/ \
		$(TESTBED_IMAGE) bash isso/js/tests/screenshots/compare-hashes.sh -u

clean:
	rm -f $(ISSO_JS_DST)
	rm -rf $(DOCS_HTML_DST)
	rm -rf $(APIDOC_DST)
	rm -rf .pytest_cache/
	rm -rf .coverage

.PHONY: apidoc apidoc-init clean coverage docker docker-compare-screenshots docker-generate-screenshots docker-update-screenshots docker-js-unit docker-js-integration docker-push docker-testbed docker-testbed-push init test
