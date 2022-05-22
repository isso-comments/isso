/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

// Set up our document body
document.body.innerHTML =
  '<div id=isso-thread></div>' +
  '<script ' +
    'src="http://isso.api/js/embed.min.js" ' +
    'data-isso="/" ' +
    '></script>';

const $ = require("app/dom");

beforeEach(() => {
  // Clean up any leftover postboxes
  if ($('.isso-postbox')) {
    $('.isso-postbox').remove();
  }
});

// TODO: Skipped due to interfering with next test
test.skip('Create Postbox with reply notifications disabled by default', () => {
  const isso = require("app/isso");
  const config = require("app/config");
  const i18n = require("app/i18n");
  const template = require("app/template");
  template.set("conf", config);
  template.set("i18n", i18n.translate);

  expect(config['reply-notifications-default-enabled']).toBe(false);

  var isso_thread = $('#isso-thread');
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-notification-section input[type="checkbox"]',
           isso_thread).checked()).toBe(false);
});

// TODO: Due to the current nature of config.js immmediately initializing and
// not being able to re-initialize, this test can only be run in isolation
test('Create Postbox with reply notifications enabled by default', () => {
  var script_tag = document.getElementsByTagName('script')[0];
  script_tag.setAttribute('data-isso-reply-notifications-default-enabled', 'true');

  expect(script_tag.getAttribute('data-isso-reply-notifications-default-enabled'))
    .toBe('true');

  const isso = require("app/isso");
  const config = require("app/config");
  const i18n = require("app/i18n");
  const template = require("app/template");
  template.set("conf", config);
  template.set("i18n", i18n.translate);

  expect(config['reply-notifications-default-enabled']).toBe(true);

  expect($('.isso-postbox')).toBe(null);

  var isso_thread = $('#isso-thread');
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-postbox')).toBeTruthy();

  expect($('.isso-notification-section input[type="checkbox"]',
           isso_thread).checked()).toBe(true);
});
