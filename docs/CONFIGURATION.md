Isso Configuration
==================

The Isso configuration file is an INI-style textfile. You can point Isso to
your configuration file either with `-c path/to/isso.cfg` or with a environment
variable set to the *absolute* path.

The configuration has several sections: *general* for general application behavior,
*server* to specify host and port when not using uWSGI, *SMTP* to send mail
notifications (heavily recommended to use) and *guard*, a naive solution for spam
and abuse detection.

## Example Configuration

    [general]
    dbpath = /var/lib/isso/comments.db
    host = https://example.tld/
    [server]
    port = 1234

For more information on the syntax, refer to [Wikipedia: INI file][1]

[1]: https://en.wikipedia.org/wiki/INI_file

## general

dbpath
: location to the SQLite3 database, defaults to /tmp/isso.db (may pruned
after system restart, so use a proper location).

secretkey
: session key. If you restart the application several times per hour for
whatever reason, use a static key. Defaults to a random string per application
start.

host
: location to your website or blog. When you start Isso, it will try to
establish a connection to your website (a simple HEAD request). If this
check fails, none can comment on your website.

max-age
: time to allow users to remove or edit their comments. Defaults to `900`
seconds (15 minutes).

## server (not applicable for uWSGI)

host
: interface to listen on, defaults to `localhost`.

port
: port to listen on, defaults to 8080.

reload
: reload application, when editing the source code (only useful for developers),
disabled by default.

## SMTP

username
: self-explanatory

password
: self-explanatory (yes, plain text, create a dedicated account for notifications.

host
: server host, defaults to `localhost`.

port
: server port, defaults to `465`.

ssl
: use SSL, defaults to `on`.

to
: recipient address

from
: sender address

## guard

enabled
: defaults to `on`.
