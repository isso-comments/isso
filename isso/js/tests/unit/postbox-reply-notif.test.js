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

const isso = require("app/isso");
const $ = require("app/dom");
const config = require("app/config");
const i18n = require("app/i18n");
const template = require("app/template");
template.set("conf", config);
template.set("i18n", i18n.translate);

test('Create Postbox with reply notifications disabled by default', () => {
  var isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-notification-section input[type="checkbox"]',
           isso_thread).checked).toBeFalse;
});

test('Create Postbox with reply notifications enabled by default', () => {
  var script_tag = document.getElementsByTagName('script')[0];
  script_tag.setAttribute('data-isso-reply-notifications-default-enabled', 'true');

  var isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-notification-section input[type="checkbox"]',
           isso_thread).checked).toBeTrue;
});
