/* Puppeteer End-to-End Integration Tests
 *
 * Puppeteer is a tool to use a (headless) Chrome browser to simulate client
 * interaction.
 *
 * See also:
 * https://puppeteer.github.io/puppeteer/
 * https://jestjs.io/docs/configuration
 */

// https://github.com/smooth-code/jest-puppeteer/issues/160#issuecomment-491975158
// For `jest-puppeteer` package, currently empty but good to have
process.env.JEST_PUPPETEER_CONFIG = require.resolve('./jest-puppeteer.config.js');

const config = {
  /* puppeteer end-to-end integration testing
   * https://jestjs.io/docs/configuration#preset-string */
  preset: "jest-puppeteer",

  // Highlight failing lines in GH Actions reports
  // https://jestjs.io/docs/configuration#reporters-arraymodulename--modulename-options
  "reporters": ["default", "github-actions"],
};

module.exports = config;
