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

test('Website field hidden when website-field=false', () => {
  document.body.innerHTML =
    '<div id="isso-thread"></div>' +
    '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");

  const config = Object.assign({}, require("app/config"), {'website-field': false});

  const i18n = require("app/i18n");
  const svg = require("app/svg");
  const template = require("app/template");

  template.set("conf", config);
  template.set("i18n", i18n.translate);
  template.set("pluralize", i18n.pluralize);
  template.set("svg", svg);

  const isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');
  isso_thread.append(new isso.Postbox(null));

  // Website input should not be present
  expect(document.querySelector('#isso-postbox-website')).toBeNull();
  expect(document.querySelector('[name=website]')).toBeNull();

  // Author and email fields should still be present
  expect(document.querySelector('#isso-postbox-author')).not.toBeNull();
  expect(document.querySelector('#isso-postbox-email')).not.toBeNull();
});

test('Website field shown when website-field=true (default)', () => {
  document.body.innerHTML =
    '<div id="isso-thread"></div>' +
    '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");

  const config = Object.assign({}, require("app/config"), {'website-field': true});

  const i18n = require("app/i18n");
  const svg = require("app/svg");
  const template = require("app/template");

  template.set("conf", config);
  template.set("i18n", i18n.translate);
  template.set("pluralize", i18n.pluralize);
  template.set("svg", svg);

  const isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');
  isso_thread.append(new isso.Postbox(null));

  // Website input should be present
  expect(document.querySelector('#isso-postbox-website')).not.toBeNull();
  expect(document.querySelector('[name=website]')).not.toBeNull();
});
