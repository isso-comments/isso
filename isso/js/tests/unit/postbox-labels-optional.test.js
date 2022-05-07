/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

test('"(optional)" labels in Postox vanish if require-author/-email set', () => {
  // Set up our document body
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"'
          + 'data-isso-lang="de"' // falls back to "en" for placeholders
          + '></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");

  var config = require("app/config");
  config['require-author'] = true;
  config['require-email'] = true;

  const i18n = require("app/i18n");
  const svg = require("app/svg");

  const template = require("app/template");

  template.set("conf", config);
  template.set("i18n", i18n.translate);
  template.set("pluralize", i18n.pluralize);
  template.set("svg", svg);

  var isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');
  isso_thread.append(new isso.Postbox(null));

  expect($("#isso-postbox-author").placeholder).toBe('John Doe');
  expect($("#isso-postbox-email").placeholder).toBe('johndoe@example.com');
  // Instead of "Name (optional)"
  expect($("[for='isso-postbox-author']").textContent).toBe('Name');
  // Instead of "E-mail (optional)"
  expect($("[for='isso-postbox-email']").textContent).toBe('E-Mail');
});
