var html = function (globals) {
  // De-structure globals dict
  ({i18n, comment, conf, datetime, humanize, svg} = {...globals});
  return "" +
"<div class='isso-comment' id='isso-" + comment.id + "'>"
+ (conf.gravatar ? "<div class='avatar'><img src='" + comment.gravatar_image + "'></div>" : '')
+ (conf.avatar ? "<div class='avatar'><svg data-hash='" + comment.hash + "'</svg></div>" : '')
+ "<div class='text-wrapper'>"
  + "<div class='isso-comment-header' role='meta'>"
    + (comment.website
        ? "<a class='author' href='" + comment.website + "' rel='nofollow'>"
             + (comment.author ? comment.author : i18n('comment-anonymous')) + "</a>"
        : "<span class='author'>"
             + (comment.author  ? comment.author : i18n('comment-anonymous')) + "</span>")
     + "<span class='spacer'>&bull;</span>"
     + "<a class='permalink' href='#isso-" + comment.id + "'>"
       + "<time title='" + humanize(comment.created) + "' datetime='" + datetime(comment.created) + "'>" + humanize(comment.created) + "</time>"
     + "</a>"
     + "<span class='note'>"
         + (comment.mode == 2 ? i18n('comment-queued') : (comment.mode == 4 ? i18n('comment-deleted') : ''))
     + "</span>"
  + "</div>" // .text-wrapper
  + "<div class='text'>"
    + (comment.mode == 4 ? '<p>&nbsp;</p>' : comment.text)
  + "</div>" // .text
  + "<div class='isso-comment-footer'>"
    + (conf.vote
        ? "<a class='upvote' href='#'>" + svg['arrow-up'] + "</a>"
          + "<span class='spacer'>|</span>"
          + "<a class='downvote' href='#'>" + svg['arrow-down'] + "</a>"
        : '')
     + "<a class='reply' href='#'>" + i18n('comment-reply') + "</a>"
     + "<a class='edit' href='#'>" + i18n('comment-edit') + "</a>"
     + "<a class='delete' href='#'>" + i18n('comment-delete') + "</a>"
  + "</div>" // .isso-comment-footer
  + "<div class='isso-follow-up'></div>"
+ "</div>" // .text-wrapper
+ "</div>" // .isso-comment
};
module.exports = html;
