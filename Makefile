ISSO = "isso/js"

all: admin client

init:
	git clone https://github.com/posativ/promisejs.git $(ISSO)/promise.js
	(cd $(ISSO) && ender build jeesh)
	(cd $(ISSO) && ender add promise.js)
	rm -rf $(ISSO)/promise.js

admin:
	cat $(ISSO)/ender.js $(ISSO)/isso.js $(ISSO)/utils.js $(ISSO)/admin.js > $(ISSO)/_.js
	yuicompressor --type js --charset utf-8 $(ISSO)/_.js -o $(ISSO)/interface.js

	rm $(ISSO)/_.js

client:
	cat $(ISSO)/ender.js $(ISSO)/isso.js $(ISSO)/utils.js $(ISSO)/client.js > $(ISSO)/_.js
	yuicompressor --type js --charset utf-8 $(ISSO)/_.js -o $(ISSO)/embed.js

	rm $(ISSO)/_.js
