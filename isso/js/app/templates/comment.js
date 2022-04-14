var html = function (globals) {
  var i18n = globals.i18n;
  var comment = globals.comment;
  var conf = globals.conf;
  var datetime = globals.datetime;
  var humanize = globals.humanize;
  var svg = globals.svg;

  var author = comment.author ? comment.author : i18n('comment-anonymous');

  return "" +
"<div class='isso-comment' id='isso-" + comment.id + "'>"
+ (conf.gravatar ? "<div class='isso-avatar'><img src='" + comment.gravatar_image + "'></div>" : '')
+ (conf.avatar ? "<div class='isso-avatar'><svg data-hash='" + comment.hash + "'</svg></div>" : '')
+ "<div class='isso-text-wrapper'>"
  + "<div class='isso-comment-header' role='meta'>"
    + (comment.website
        ? "<a class='isso-author' href='" + comment.website + "' rel='nofollow'>" + author + "</a>"
        : "<span class='isso-author'>" + author + "</span>")
     + "<span class='isso-spacer'>&bull;</span>"
     + "<a class='isso-permalink' href='#isso-" + comment.id + "'>"
       + "<time title='" + humanize(comment.created) + "' datetime='" + datetime(comment.created) + "'>" + humanize(comment.created) + "</time>"
     + "</a>"
     + "<span class='isso-note'>"
         + (comment.mode == 2 ? i18n('comment-queued') : (comment.mode == 4 ? i18n('comment-deleted') : ''))
     + "</span>"
  + "</div>" // .text-wrapper
  + "<div class='isso-text'>"
    + (comment.mode == 4 ? '<p>&nbsp;</p>' : comment.text)
  + "</div>" // .text
  + "<div class='isso-comment-footer'>"
    + (conf.vote
        ? "<a class='isso-upvote' href='#'>" + svg['arrow-up'] + "</a>"
          + "<span class='isso-spacer'>|</span>"
          + "<a class='isso-downvote' href='#'>" + svg['arrow-down'] + "</a>"
        : '')
     + "<a class='isso-reply' href='#'>" + i18n('comment-reply') + "</a>"
     + "<a class='isso-edit' href='#'>" + i18n('comment-edit') + "</a>"
     + "<a class='isso-delete' href='#'>" + i18n('comment-delete') + "</a>"
  + "</div>" // .isso-comment-footer
  + "<div class='isso-follow-up'></div>"
+ "</div>" // .text-wrapper
+ "</div>" // .isso-comment
};
module.exports = html;
