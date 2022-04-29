/* Puppeteer End-to-End Integration Tests
 *
 * Puppeteer is a tool to use a (headless) Chrome browser to simulate client
 * interaction.
 *
 * See also:
 * https://puppeteer.github.io/puppeteer/
 * https://jestjs.io/docs/configuration
 */

const config = {
  /* puppeteer end-to-end integration testing
   * https://jestjs.io/docs/configuration#preset-string */
  preset: "jest-puppeteer",
};

module.exports = config;
