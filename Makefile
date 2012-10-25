all:

init:
	(cd isso/js && ender build jeesh reqwest)

js:
	cat isso/js/ender.js isso/js/isso.js > _.js
	yuicompressor --type js --charset utf-8 _.js -o isso/js/embed.js
	rm _.js
