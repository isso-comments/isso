<%inherit file="base.mako"/>

<%block name="js">
    <%include file="admin.js"/>
</%block>

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

    <article class="isso" data-path="${quote(comment.path)}" data-id="${comment.id}">
        <header>
            <!-- <span class="title"><a href="${comment.path}">${comment.path}</a></span> -->
            <span class="created">${strftime('%a %d %B %Y', gmtime(comment.created))}</span>
            <span class="author">
                % if comment.website:
                    <a href="${comment.website}">${comment.author}</a>
                % else:
                    ${comment.author}
                % endif
            </span>
            <span class="email">${comment.email}</span>
        </header>

        <div class="text">
            ${app.markup.convert(comment.text)}
        </div>

        <footer>
            % if comment.pending:
                <a href="#">Approve</a> |
            % endif
            <a href="#">Delete</a>
        </footer>
    </article>
</%def>

<h1>Dashboard</h1>

<div>
    <h2>Pending</h2>
    <span class="limit">
        [ <a href="?${query(pendinglimit=10)}">10</a>
        | <a href="?${query(pendinglimit=20)}">20</a>
        | <a href="?${query(pendinglimit=100000)}">All</a> ]
    </span>

    % for comment in app.db.recent(limit=get('pendinglimit', int), mode=2):
        ${make(comment)}
    % endfor
</div>

<div>
    <h2 class="recent">Recent</h2>
    <span class="limit">
        [<a href="?${query(recentlimit=10)}">10</a>
        | <a href="?${query(recentlimit=20)}">20</a>
        | <a href="?${query(recentlimit=100000)}">All</a>]
    </span>

    % for comment in app.db.recent(limit=get('recentlimit', int) or 20, mode=5):
        ${make(comment)}
    % endfor

</div>
