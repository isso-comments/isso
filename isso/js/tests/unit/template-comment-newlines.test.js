/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

/* Test rendered code blocks inside "comment" template
 * See https://github.com/posativ/isso/discussions/856
 * and https://github.com/posativ/isso/pull/857
 */

// Set up our document body
document.body.innerHTML =
  '<div id=isso-thread></div>' +
  '<script ' +
    'src="http://isso.api/js/embed.min.js" ' +
    'data-isso="/" ' +
    '></script>';

const isso = require("app/isso");
const $ = require("app/dom");
const config = require("app/config");
const template = require("app/template");

const i18n = require("app/i18n");
const svg = require("app/svg");

template.set("conf", config);
template.set("i18n", i18n.translate);
template.set("pluralize", i18n.pluralize);
template.set("svg", svg);

test('Simple comment text should render on one line', () => {
  let comment = {
      "id": 1,
      "created": 1651788192.4473603,
      "mode": 1,
      "text": "<p>A comment</p>",
      "author": "John",
      "website": "http://website.org",
      "hash": "4505c1eeda98",
  }
  let rendered = template.render("comment", {"comment": comment});
  let el = $.htmlify(rendered);
  expect($('.isso-text', el).innerHTML).toMatchSnapshot();

});

test('Code blocks in rendered comment should not be clipped', () => {
  let comment = {
      "id": 2,
      "created": 1651788192.4473603,
      "mode": 1,
      "text": "<p>A comment with</p>\n<pre><code>code blocks\nNew line: preformatted\n\nDouble newline\n</code></pre>",
      "author": "John",
      "website": "http://website.org",
      "hash": "4505c1eeda98",
  }
  let rendered = template.render("comment", {"comment": comment});
  let el = $.htmlify(rendered);
  expect($('.isso-text', el).innerHTML).toMatchSnapshot();
});
