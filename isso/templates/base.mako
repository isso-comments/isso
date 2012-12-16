<!DOCTYPE html>
<head>
    <title><%block name="title" /></title>
    <meta charset="utf-8" />
    <script type="text/javascript" src="/js/ender.js"></script>
    <script type="text/javascript">
        <%block name="js" />
    </script>
    <link rel="stylesheet" type="text/css" href="/static/style.css" />
    <style>

        /* ================ */
        /* = The 1Kb Grid = */     /* 12 columns, 60 pixels each, with 20 pixel gutter */
        /* ================ */

        .grid_1  { width: 60px; }
        .grid_2  { width: 140px; }
        .grid_3  { width: 220px; }
        .grid_4  { width: 300px; }
        .grid_5  { width: 380px; }
        .grid_6  { width: 460px; }
        .grid_7  { width: 540px; }
        .grid_8  { width: 620px; }
        .grid_9  { width: 700px; }
        .grid_10 { width: 780px; }
        .grid_11 { width: 860px; }
        .grid_12 { width: 940px; }

        .column {
            margin: 0 10px;
            overflow: hidden;
            float: left;
            display: inline;
        }
        .row {
            width: 960px;
            margin: 0 auto;
            overflow: hidden;
        }
        .row .row {
            margin: 0 -10px;
            width: auto;
            display: inline-block;
        }

        * {
            margin: 0;
            padding: 0;
        }

        body {
            font-size: 1em;
            line-height: 1.4;
            margin: 20px 0 0 0;

            background: url(/static/simple-clouds.jpg) no-repeat center center fixed;
        }

        body > h1 {
            text-align: center;
            padding: 8px 0 8px 0;
            background-color: yellowgreen;
        }

        article {
            background-color: rgb(245, 245, 245);
            box-shadow: 0px 0px 4px 0px;
            border-radius: 2px;
        }

        article header {
            font-size: 1.1em;
        }

        article .options {
            margin: 8px;
            padding-bottom: 40px
        }

        article .text, article header {
            padding: 8px 16px 8px 16px;
        }

        .text p {
            margin-bottom: 10px;
            text-align: justify;
        }

        .recent, .pending {
            padding: 10px 40px 10px 40px;
            box-shadow: 0px 0px 2px 0px;
            border-radius: 4px;
            margin: 2px auto 2px auto;
        }

        .green {
            background-color: #B7D798;
        }

        .red {
            background-color: #D79998;
        }

        body > footer {
            border-top: 1px solid #ccc;
            padding-top: 8px;

            text-align: center;
        }

        .approve, .delete {
            padding-top: 10px;
            padding: 5px;
            border: 1px solid #666;
            color: #000;
            text-decoration: none;
        }

        .buttons {
            padding-top: 10px;
        }

        <%block name="style" />
    </style>
</head>
<body>
    ${self.body()}
</body>