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
    enabled = true

Users authenticate by clicking the OpenID button and typing in their
OpenID identifier. To do so the user must have an OpenID provider that
supports OpenID Connect 1.0 (earlier versions OpenID 1.0 and OpenID
2.0 are not supported).

Facebook
--------

To enable Facebook login, you must first create a Facebook App by
visiting [Facebook for Developers](https://developers.facebook.com/)
and choosing `My Apps->Add a New App`. On the `Product Setup` screen,
add `Facebook Login`. Make sure `Client OAuth Login` and `Web OAuth
Login` are enabled and fill in your site's URL under `Valid OAuth
redirect URIs`. Next, go to your app's general settings
(`Settings->Basic`) and fill in your site's URL also under `Site URL`
(you may have to add `Web` as a platform first). Then take note of the
`App ID` and `App Secret` that Facebook has generated for your app,
and add the following settings to your Isso configuration file:

    [facebook]
    enabled = true
    app-id = <Your App ID>
    app-secret = <Your App Secret>

Google
------

To enable Google login, you must first create a Google App by visiting
the [Google API Console](https://console.developers.google.com/) and
choosing `Create Project`. Under `Credentials`, choose `Create
Credentials->OAuth client ID`, and then choose `Web application`. Then
take note of the `Client ID` that Google has generated for you, and
add the following settings to your Isso configuration file:

    [google]
    enabled = true
    client-id = <Your Client ID>

Roles
-----

It may be desirable to show that some users have a special role on the
site, such as moderators. Such roles are defined in the Isso
configuration file like this:

    [roles]
    web-master = Web master, google:107686722757000000000
    moderator = Moderator, facebook:10208666300000000 openid:acct:joe@example.com

The name of each "setting" in the role section can be chosen
arbitrarily. The first line in the example ensures that all comments
made by the person who authenticates with Google and has Google ID
107686722757000000000 gets a label saying "Web master" next to
them. Two users are then defined as Moderators. The label uses the
name of the setting ("web-master" in the first example) as its CSS
class in case you want to control the appearance of each of them.
