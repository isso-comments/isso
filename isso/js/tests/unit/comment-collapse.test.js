/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

// globals.offset.localTime() will be passed to i18n.ago()
// localTime param will then be called as localTime.getTime()
jest.mock('app/globals', () => ({
  offset: {
    localTime: jest.fn(() => ({
      getTime: jest.fn(() => 0),
    })),
  },
}));

beforeEach(() => {
  jest.resetModules();
  document.body.innerHTML = '';
});

const parent = {
  "id": 1,
  "created": 1651788192.4473603,
  "mode": 1,
  "text": "<p>A long comment</p>",
  "author": "John",
  "hash": "4505c1eeda98",
  "parent": null,
  "replies": [{
    "id": 2,
    "created": 1651788192.4473603,
    "mode": 1,
    "text": "<p>A reply</p>",
    "author": "Jane",
    "hash": "1a2b3c4d5e6f",
    "parent": 1,
  }],
  "hidden_replies": 0,
};

const setup = (attrs, hidden_replies) => {
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js"'
          + ' data-isso="/"'
          + ' data-isso-id="1"' + (attrs || '') + '></script>';

  const isso = require("app/isso");
  const $ = require("app/dom");
  const config = require("app/config");
  const template = require("app/template");
  const i18n = require("app/i18n");
  const svg = require("app/svg");

  template.set("conf", config);
  template.set("i18n", i18n.translate);
  template.set("pluralize", i18n.pluralize);
  template.set("svg", svg);

  $('#isso-thread').append('<div id="isso-root"></div>');
  const comment = JSON.parse(JSON.stringify(parent));
  comment.hidden_replies = hidden_replies || 0;
  isso.insert({ comment: comment, scrollIntoView: false, offset: 0 });

  return isso;
};

test('Collapse toggle hides a comment and its replies', () => {
  setup();

  const comment = document.querySelector('#isso-1');
  const toggle = document.querySelector('#isso-1 > .isso-text-wrapper > .isso-comment-header > .isso-collapse');
  const note = document.querySelector('#isso-1 > .isso-text-wrapper > .isso-comment-header > .isso-collapsed-note');

  expect(toggle).not.toBeNull();
  expect(toggle.getAttribute('aria-expanded')).toBe('true');
  expect(comment.classList.contains('isso-collapsed')).toBe(false);

  toggle.click();
  expect(comment.classList.contains('isso-collapsed')).toBe(true);
  expect(toggle.getAttribute('aria-expanded')).toBe('false');
  expect(toggle.getAttribute('title')).toBe('Expand');
  expect(toggle.textContent).toBe('[+]');
  expect(note.textContent).toBe('1 reply');

  toggle.click();
  expect(comment.classList.contains('isso-collapsed')).toBe(false);
  expect(toggle.getAttribute('aria-expanded')).toBe('true');
  expect(toggle.getAttribute('title')).toBe('Collapse');
  expect(toggle.textContent).toBe('[−]');
  expect(note.textContent).toBe('');
});

test('Collapsed reply count includes replies not loaded yet', () => {
  setup('', 7);

  document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapse').click();

  expect(document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapsed-note').textContent).toBe('8 replies');
});

test('Clicking the reply count note expands the comment', () => {
  setup();

  document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapse').click();
  document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapsed-note').click();

  expect(document.querySelector('#isso-1').classList.contains('isso-collapsed')).toBe(false);
  expect(document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapsed-note').textContent).toBe('');
});

test('Collapsing a reply only affects that reply', () => {
  setup();

  document.querySelector('#isso-2 .isso-collapse').click();

  expect(document.querySelector('#isso-2').classList.contains('isso-collapsed')).toBe(true);
  expect(document.querySelector('#isso-1').classList.contains('isso-collapsed')).toBe(false);
  expect(document.querySelector('#isso-2 .isso-collapsed-note').textContent).toBe('');
});

test('expand_ancestors expands collapsed parents of a linked comment', () => {
  const isso = setup();

  document.querySelector('#isso-1 > .isso-text-wrapper .isso-collapse').click();
  expect(document.querySelector('#isso-1').classList.contains('isso-collapsed')).toBe(true);

  expect(isso.expand_ancestors(document.querySelector('#isso-2'))).toBe(true);
  expect(document.querySelector('#isso-1').classList.contains('isso-collapsed')).toBe(false);
  expect(isso.expand_ancestors(document.querySelector('#isso-2'))).toBe(false);
});

test('No collapse toggle when data-isso-collapsible="false"', () => {
  setup(' data-isso-collapsible="false"');

  expect(document.querySelector('.isso-collapse')).toBeNull();
  expect(document.querySelector('.isso-collapsed-note')).toBeNull();
});
