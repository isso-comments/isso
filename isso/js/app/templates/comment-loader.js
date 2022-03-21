var html = function (globals) {
  // De-structure globals dict
  ({comment, pluralize} = {...globals});
  return "" +
"<div class='isso-comment-loader' id='isso-loader-" + comment.name + "'>"
+ "<a class='load_hidden' href='#'>" + pluralize('comment-hidden', comment.hidden_replies) + "</a>"
+ "</div>"
};
module.exports = html;
