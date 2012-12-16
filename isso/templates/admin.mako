<%inherit file="base.mako"/>

<%
    from time import strftime, gmtime

    from urllib import quote, urlencode
    from urlparse import parse_qsl

    def query(**kw):
         qs = dict(parse_qsl(request.query_string))
         qs.update(kw)
         return urlencode(qs)

    def get(name, convert):
        limit = request.args.get(name)
        return convert(limit[0]) if limit is not None else None
%>

<%block name="title">
    Isso – Dashboard
</%block>


<%def name="make(comment)">

    <article class="isso column grid_12" data-path="${quote(comment.path)}" data-id="${comment.id}">
        <div class="row">
            <div class="column grid_9">
                <header>
                    <span class="title"><a href="${comment.path}">${comment.path}</a></span>
                </header>

                <div class="text">
                    ${app.markup.convert(comment.text)}
                </div>

            </div>

            <div class="column grid_3 options">

                <ul>
                    <li>${strftime('%d. %B %Y um %H:%M', gmtime(comment.created))}</li>
                    <li>von <em>${comment.author}</em></li>
                    % if comment.website:
                        <li><a href="${comment.website}">${comment.website}</a></li>
                    % endif

                </ul>

                <div class="row buttons">
                    <a href="#" class="red delete column grid_1">Delete</a>
                    % if comment.pending:
                        <a href="#" class="green approve column grid_1">Approve</a>
                    % endif
                </div>
            </div>
        </div>
    </article>
</%def>

<div class="row pending red">
    <div class="column grid_9">
        <h2>Pending</h2>
    </div>

    <div class="column grid_3">
        <span class="limit">
            [ <a href="?${query(pendinglimit=10)}">10</a>
            | <a href="?${query(pendinglimit=20)}">20</a>
            | <a href="?${query(pendinglimit=100000)}">All</a> ]
        </span>
    </div>

</div>

<div class="row" id="pending">
    % for comment in app.db.recent(limit=get('pendinglimit', int), mode=2):
        ${make(comment)}
    % endfor
</div>

<div class="row recent green">
    <div class="column grid_9">
        <h2>Recent</h2>
    </div>
    <div class="column grid_3">
        <span class="limit">
            [ <a href="?${query(recentlimit=10)}">10</a>
            | <a href="?${query(recentlimit=20)}">20</a>
            | <a href="?${query(recentlimit=100000)}">All</a> ]
        </span>
    </div>
</div>

<div class="row" id="approved">
    % for comment in app.db.recent(limit=get('recentlimit', int) or 20, mode=5):
        ${make(comment)}
    % endfor
</div>

<footer class="row">

    <p><a href="https://github.com/posativ/isso">Isso</a> – Ich schrei sonst!</p>

</footer>
