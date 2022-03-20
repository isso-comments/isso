var html = function (globals) {
  var comment = globals.comment;
  var pluralize = globals.pluralize;

  return "" +
"<div class='isso-comment-loader' id='isso-loader-" + comment.name + "'>"
+ "<a class='isso-load-hidden' href='#'>" + pluralize('comment-hidden', comment.hidden_replies) + "</a>"
+ "</div>"
};
module.exports = html;
