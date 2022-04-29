/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

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
