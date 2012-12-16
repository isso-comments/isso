<%inherit file="base.mako"/>

<%block name="title">
    Isso – Login
</%block>

<%block name="style">

    #login {
        margin: 280px 270px 0 270px;
        padding: 30px;
        background-color: rgb(245, 245, 245);
        box-shadow: 0px 0px 4px 0px;
        border-radius: 8px;
        text-align: center;
    }

    .button {
        border: 1px solid #006;
        margin-left: 2px;
        padding: 2px 4px 2px 4px;
    }

    #login input {
        margin-top: 8px;
        text-align: center;
    }
    #login input:-moz-placeholder, #login input::-webkit-input-placeholder {} {
        color: #CCC;
    }
</%block>

<!-- login form -->
<div id="login">
  <form action="/" method="post">
    <input name="secret" placeholder="secret" type="password" />
    <input type="submit" name="submit" value="Login" class="button" />
  </form>
</div>
