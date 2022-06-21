/* https://jestjs.io/docs/configuration
 *
 * Best practices by mailchimp:
 * https://mailchimp.com/developer/open-commerce/docs/testing-requirements/
 * When writing your test:
 *  - Do not add extra describe blocks. Jest tests are automatically file-scoped,
 *    so a file that performs a single test does not need a describe block in it.
 *    You may add multiple describe blocks to group related tests within one
 *    file, but you should not have a file with only a single describe block in
 *    it.
 *  - Always use test() instead of it() to define test functions.
 *  - Do not import describe, test, jest, jasmine, or expect. They are automatic
 *    globals in all test files.
 *  - Use arrow functions for all describe and test functions.
 *  - Use Jest’s built-in expect function for assertions.
 *  - You might need to test asynchronous code: functions that either return a
 *    Promise or take a callback argument. You should use Promises unless you
 *    need to use a callback, such as when the API of another package requires
 *    it. When using callbacks, make sure to add a done argument to your test
 *    function and call done when all testing is complete.
 */

const config = {
  /* modulePaths:
   * An alternative API to setting the NODE_PATH env variable, modulePaths is
   * an array of absolute paths to additional locations to search when
   * resolving modules. Use the <rootDir> string token to include the path to
   * your project's root directory. Example: ["<rootDir>/app/"].
   */
  modulePaths: ["<rootDir>"],
  /* rootDir already set to pwd when running jest with this config as arg */
  moduleNameMapper: {
    "\.svg$": "<rootDir>/tests/mocks/fileTransformer.js",
  },

  /* Run tests in a virtual DOM environment
   * See https://jestjs.io/docs/tutorial-jquery
   * -> use per-file testEnvironment stanza instead
   */
  //testEnvironment: "jsdom",

  "globalSetup": "<rootDir>/tests/setup/global-setup.js",

  // Highlight failing lines in GH Actions reports
  // https://jestjs.io/docs/configuration#reporters-arraymodulename--modulename-options
  "reporters": ["default", "github-actions"],
};

module.exports = config;
