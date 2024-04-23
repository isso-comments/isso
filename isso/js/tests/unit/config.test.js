/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

beforeEach(() => {
  jest.resetModules();
  document.body.innerHTML = '';
});

test("Client configuration - no languages", () => {
  // Mock navigator.languages = []
  global.languages = jest.spyOn(navigator, "languages", "get")
  global.languages.mockReturnValue([]);

  // Mock navigator.language = null
  global.language = jest.spyOn(navigator, "language", "get")
  global.language.mockReturnValue(null);

  let config = require("app/config");

  /* Expected:
   * - no config["lang"]
   * - navigator.languages empty
   *   - fall back on navigator.language
   *     - navigator.language empty
   *        - fall back on navigator.userLanguage
   *            - navigator.userLanguage empty
   *              (jsdom doesn't set it)
   * - config["default-lang"] = "en"
   * - final manual insertion of "en"
   */
  let expected_langs = ["en", "en"];

  expect(config["langs"]).toStrictEqual(expected_langs);
});

test("data-isso-* i18n strings should be accepted with newline characters", () => {

  document.body.innerHTML =
      '<div id=isso-thread></div>' +
      // Note: `src` and `data-isso` need to be set,
      // else `api` fails to initialize!
      '<script src="http://isso.api/js/embed.min.js"'
      + ' data-isso="/"'
      + '</script>';

  var script_tag = document.getElementsByTagName('script')[0];
  script_tag.setAttributeNS(null, 'data-isso-num-comments-text-en', "One comment\\n{{ n }} comments");

  const config = require("app/config");

  expect(config['num-comments-text-en']).toMatch("One comment\n{{ n }} comments");
});
