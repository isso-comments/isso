Sub-URI
=======

You can run Isso on the same domain as your website, which circumvents issues
originating from CORS_. Also, privacy-protecting browser addons such as
`Request Policy`_ wont block comments.

.. code-block:: nginx

    server {
        listen       [::]:80;
        listen       [::]:443 ssl;
        server_name  example.tld;
        root         /var/www/example.tld;

        location /isso {
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Script-Name /isso;
            proxy_set_header Host $host;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_pass http://localhost:8080;
        }
    }

Now, the website integration is just as described in :doc:`../quickstart` but
with a different location.

.. _CORS: https://developer.mozilla.org/en/docs/HTTP/Access_control_CORS
.. _Request Policy: https://www.requestpolicy.com/
