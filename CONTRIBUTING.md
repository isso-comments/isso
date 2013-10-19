Contributing
============

I appreciate any help and love pull requests. Here are some things
you need to respect:

* no hard-wired external services
* no support for ancient browsers (e.g. IE6-9)

Reporting Issues
----------------

### Disqus import fails

If `isso import /path/to/disqus.xml` fails, please do *NOT* attach the raw
dump file to GH:Issues. Please anonymize all IP addresses inside the `<ipAddress>`
tag first, as second step, replace all email addresses with a generic one (
email tag).

### embed.min.js-related issues

In case of a JavaScript traceback, please setup Isso in development mode
described below. Otherwise it is very hard to "guess" the reason.

### isso-related issues

Copy and paste traceback into a ticket and provide some details of your usage.


Development
-----------

If you want to hack on Isso or track down issues, there's an alternate
way to set up Isso. It requires a lot more dependencies and effort.

Requirements:

- Python 2.6, 2.7 or 3.3
- Ruby 1.8 or higher
- Node.js, [NPM](https://npmjs.org/) and [Bower](http://bower.io/)

On Debian/Ubuntu install the following packages

    ~> sudo aptitude install python-setuptools python-dev npm ruby
    ~> ln -s /usr/bin/nodejs /usr/bin/node

Get the repository:

    ~> git clone https://github.com/posativ/isso.git
    ~> cd isso/

Install `virtualenv` and create a new environment for Isso (recommended):

    ~> pip install virtualenv
    ~> virtualenv .
    ~> source ./bin/activate

Install Isso dependencies:

    ~> python setup.py develop
    ~> isso run

Compile SCSS to CSS:

    ~> gem install sass
    ~> scss --watch isso/css/isso.scss

Install JS components:

    ~> cd isso/js
    ~> bower install almond q requirejs requirejs-domready requirejs-text


Integration
-----------

```html
<link rel="stylesheet" href="/isso/static/isso.css" />
<script src="/isso/js/config.js"></script>
<script data-main="/isso/js/embed" src="/isso/js/components/requirejs/require.js"></script>
```


Optimization
------------

    ~> npm install -g requirejs uglifyjs
    ~> cd isso/js
    ~> r.js -o build.embed.js
    ~> r.js -o build.count.js
