ISSO = "isso/js"

all: js

init:
	git clone https://github.com/posativ/promisejs.git $(ISSO)/promise.js
	(cd $(ISSO) && ender build jeesh)
	(cd $(ISSO) && ender add promise.js)
	rm -rf $(ISSO)/promise.js

js:
	cat $(ISSO)/ender.js $(ISSO)/isso.js $(ISSO)/utils.js > $(ISSO)/_.js
	yuicompressor --type js --charset utf-8 $(ISSO)/_.js -o $(ISSO)/embed.js
	rm $(ISSO)/_.js
