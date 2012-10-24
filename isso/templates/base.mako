<!DOCTYPE html>
<head>
    <title><%block name="title" /></title>
    <meta charset="utf-8" />
    <style>
        body {

            font-size: 1em;
            line-height: 1.4;
            margin: 0 auto;
            width: 960px;
        }

        body > h1 {
            text-align: center;
        }

        <%block name="style" />
    </style>
</head>
<body>
    ${self.body()}
</body>