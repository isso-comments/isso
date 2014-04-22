define(["text!./postbox.html", "text!./comment.html", "text!./comment-loader.html"], function (postbox, comment, comment_loader) {
    return {
        postbox: postbox,
        comment: comment,
        comment_loader: comment_loader
    };
});
