Development
===========

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
<script src="/isso/js/config.js"></script>
<script data-main="/isso/js/embed" src="/isso/js/components/requirejs/require.js"></script>
```


Optimization
------------

    ~> npm install -g requirejs uglifyjs
    ~> cd isso/js
    ~> r.js -o build.embed.js
    ~> r.js -o build.count.js
