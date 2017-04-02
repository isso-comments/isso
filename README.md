Isso – a commenting server similar to Disqus
============================================

This **fork** of Isso adds possibility to login using OpenID,
Facebook, or Google. The user's name and profile picture is then
fetched and used for the comment for a more personal feel, and those
comments are authenticated so that the author can prove that he/she
wrote the comment.

Brief setup instructions for the additional features of this fork
follows below. For all other questions, see the
[web site of the mainline Isso project](https://posativ.org/isso/).

OpenID
------

To enable OpenID support, just enable it in the configuration file:

    [openid]
    enabled = false

Users authenticate by clicking the OpenID button and typing in their
OpenID identifier. To do so the user must have an OpenID provider that
supports OpenID Connect 1.0 (earlier versions OpenID 1.0 and OpenID
2.0 are not supported).

Facebook
--------

To enable Facebook login, you must first create a Facebook App by
visiting [Facebook for Developer](https://developers.facebook.com/)
and choosing `My Apps->Add a New App`. Set `Site URL` to the URL of
your web site where Isso is embedded (not the URL or port where Isso
itself listens). Then take note of the `App ID` and `App Secret` that
Facebook has generated for your app, and add the following settings to
your Isso configuration file:

    [facebook]
    enabled = true
    app-id = <Your App ID>
    app-secret = <Your App Secret>

Google
--------

To enable Google login, you must first create a Google App by visiting
the [Google API Console](https://console.developers.google.com/) and
choosing `Create Project`. Under `Credentials`, choose `Create
Credentials->OAuth client ID`. Then take note of the `Client ID` that
Google has generated for you, and add the following settings to your
Isso configuration file:

    [google]
    enabled = true
    client-id = <Your Client ID>
