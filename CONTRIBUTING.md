Contributing
============

I appreciate any help and love pull requests. Here are some things
you need to respect:

* no hard-wired external services
* no support for ancient browsers (e.g. IE6-9)

If you create a feature request, start a new branch. If you fix an issue,
start off the *master* branch and pull request against the master. I'll
cherry-pick/backport the fix onto the current legacy (maintenance) release.

To set up a development environment, see
[docs/DEVELOPMENT.md](https://github.com/posativ/isso/blob/master/docs/DEVELOPMENT.md)


Reporting Issues
----------------

*   **Disqus import fails**

    If `isso import /path/to/disqus.xml` fails, please do *NOT* attach the raw
    dump file to GH:Issues. Please anonymize all IP addresses inside the
    `<ipAddress>` tag first, as second step, replace all `<email>` addresses
    with a generic one.

    If you can't do this, please send the dump to `info@posativ.org` (you find
    my GPG key on the servers).

*   **embed.min.js-related issues**

    If you get a cryptic JavaScript error in the console, embed `embed.dev.js`
    instead of `embed.min.js` and create an issue with ±10 lines of code around
    the error.

*   **isso-related issues**

    Copy and paste traceback into a ticket and provide some details of your usage.
