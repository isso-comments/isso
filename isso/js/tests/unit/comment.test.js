/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";


test('Rendered comment should match snapshot', () => {
  // Set up our document body
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    // data-isso-id needed for insert_loader api.fetch()
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"'
          + 'data-isso-id="1"></script>';

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

  let comment = {
      "id": 2,
      "created": 1651788192.4473603,
      "mode": 1,
      "text": "<p>A comment with</p>\n<pre><code>code blocks\nNew line: preformatted\n\nDouble newline\n</code></pre>",
      "author": "John",
      "website": "http://website.org",
      "hash": "4505c1eeda98",
      "parent": null,
  }

  // globals.offset.localTime() will be passed to i18n.ago()
  // localTime param will then be called as localTime.getTime()
  jest.mock('app/globals', () => ({
    offset: {
      localTime: jest.fn(() => ({
        getTime: jest.fn(() => 0),
      })),
    },
  }));

  var isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');

  isso.insert({ comment, scrollIntoView: false, offset: 0 });

  // Will create a `.snap` file in `./__snapshots__/`.
  // Don't forget to check in those files when changing anything!
  expect(isso_thread.innerHTML).toMatchSnapshot();
});
