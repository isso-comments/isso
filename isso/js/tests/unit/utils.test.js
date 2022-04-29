/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

const utils = require("app/utils");

test("Pad string with zeros", function() {
  let to_be_padded = "12345";
  let pad_to = 10;
  let padding_char = "0";
  let expected = "0000012345"
  expect(utils.pad(to_be_padded, pad_to, padding_char)).toStrictEqual(expected);
});
