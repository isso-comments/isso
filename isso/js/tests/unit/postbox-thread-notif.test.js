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

var setup = function(overrides) {
  document.body.innerHTML =
    '<div id="isso-thread"></div>' +
    '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");

  // isso.js reads the config module itself, so override it in place
  const config = Object.assign(require("app/config"), overrides);

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
};

test('Thread notification checkbox absent by default', () => {
  setup({});

  expect(document.querySelector('[name=notification-thread]')).toBeNull();
  expect(document.querySelector('[name=notification]')).not.toBeNull();
});

test('Thread notification checkbox shown when thread-notifications=true', () => {
  setup({'thread-notifications': true, 'reply-notifications': true});

  const thread_box = document.querySelector('[name=notification-thread]');
  expect(thread_box).not.toBeNull();
  expect(thread_box.checked).toBe(false);

  // both checkboxes are offered, hidden until an email address is entered
  expect(document.querySelector('.isso-notification-reply').style.display).toBe('');
  expect(document.querySelector('.isso-notification-section').style.display).toBe('none');
});

test('Reply notification checkbox hidden when reply-notifications=false', () => {
  setup({'thread-notifications': true, 'reply-notifications': false});

  expect(document.querySelector('[name=notification-thread]')).not.toBeNull();
  expect(document.querySelector('.isso-notification-reply').style.display).toBe('none');
});

test('Notification section revealed once an email is entered', () => {
  setup({'thread-notifications': true, 'reply-notifications': true});

  const email = document.querySelector('[name=email]');
  email.value = 'test@test.example';
  email.dispatchEvent(new Event('input'));

  expect(document.querySelector('.isso-notification-section').style.display).toBe('block');
});
