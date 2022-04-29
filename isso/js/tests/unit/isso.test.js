/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

test('Create Postbox', () => {
  // Set up our document body
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");

  const config = require("app/config");
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

  // Will create a `.snap` file in `./__snapshots__/`.
  // Don't forget to check in those files when changing anything!
  expect(isso_thread.innerHTML).toMatchSnapshot();
});
