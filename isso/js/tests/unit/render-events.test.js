/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

// globals.offset.localTime() will be passed to i18n.ago()
jest.mock('app/globals', () => ({
  offset: {
    localTime: jest.fn(() => ({
      getTime: jest.fn(() => 0),
    })),
  },
}));

// embed.js's fetchComments() drives isso-thread-rendered off api.config()/
// api.fetch(); mock app/api so tests control both outcomes without a real
// XHR round-trip.
jest.mock('app/api', () => ({
  config: jest.fn(),
  fetch: jest.fn(),
  count: jest.fn(),
  endpoint: 'http://isso.api',
  feed: jest.fn(() => 'http://isso.api/feed'),
}));

var setup = function() {
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"'
          + 'data-isso-id="1"></script>';

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

  var isso_thread = $('#isso-thread');
  isso_thread.append('<div id="isso-root"></div>');

  return { isso };
};

beforeEach(() => {
  jest.resetModules();
  document.body.innerHTML = '';
});

test('isso-postbox-rendered fires when a Postbox is created', () => {
  const { isso } = setup();

  var events = [];
  document.getElementById('isso-thread')
    .addEventListener('isso-postbox-rendered', function(e) { events.push(e); });

  var postbox = new isso.Postbox(null);

  expect(events).toHaveLength(1);
  expect(events[0].detail.parent).toBeNull();
  expect(events[0].detail.element).toBe(postbox.obj);
  expect(events[0].detail.element.classList.contains('isso-postbox')).toBe(true);
});

test('isso-postbox-rendered carries the parent id for reply forms', () => {
  const { isso } = setup();

  var detail = null;
  document.addEventListener('isso-postbox-rendered', function(e) { detail = e.detail; });

  new isso.Postbox(42);

  expect(detail).not.toBeNull();
  expect(detail.parent).toBe(42);
});

test('isso-comment-rendered fires for each inserted comment', () => {
  const { isso } = setup();

  var comment = {
    "id": 2,
    "created": 1651788192.4473603,
    "mode": 1,
    "text": "<p>Hello</p>",
    "author": "John",
    "hash": "4505c1eeda98",
    "parent": null,
  };

  var detail = null;
  document.addEventListener('isso-comment-rendered', function(e) { detail = e.detail; });

  isso.insert({ comment, scrollIntoView: false, offset: 0 });

  expect(detail).not.toBeNull();
  expect(detail.comment.id).toBe(2);
  expect(detail.element.id).toBe('isso-2');
});

// embed.js dispatches isso-thread-rendered once fetchComments() settles.
// Requiring embed.js triggers its own domready(init(); fetchComments())
// call, so each test just needs to mock api.config()/api.fetch(), require
// the module, and await the event itself.
var setupEmbed = function() {
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"'
          + 'data-isso-id="1"></script>';

  var api = require("app/api");
  api.config.mockResolvedValue({ config: {} });

  return { api };
};

// Resolves once the given event fires.
var waitForEvent = function(type) {
  return new Promise(function(resolve) {
    document.addEventListener(type, resolve, { once: true });
  });
};

describe('isso-thread-rendered', () => {
  var consoleLog;

  beforeEach(() => {
    consoleLog = jest.spyOn(console, 'log').mockImplementation(() => {});
  });

  afterEach(() => {
    consoleLog.mockRestore();
  });

  test('fires with the comment count on a successful fetch', async () => {
    var { api } = setupEmbed();
    api.fetch.mockResolvedValue({
      total_replies: 2,
      hidden_replies: 0,
      replies: [
        { id: 1, created: 1651788192.4473603, mode: 1, text: "<p>Hi</p>", author: "John", hash: "aaa", parent: null },
        { id: 2, created: 1651788192.4473603, mode: 1, text: "<p>Yo</p>", author: "Jane", hash: "bbb", parent: null },
      ],
    });

    var pending = waitForEvent('isso-thread-rendered');
    require("../../embed.js");
    var event = await pending;

    expect(event.detail.count).toBe(2);
    expect(event.detail.element).toBe(document.getElementById('isso-thread'));
    expect(event.detail.error).toBeUndefined();
  });

  test('fires with count 0 and no error when the thread has no comments', async () => {
    var { api } = setupEmbed();
    api.fetch.mockResolvedValue({
      total_replies: 0,
      hidden_replies: 0,
      replies: [],
    });

    var pending = waitForEvent('isso-thread-rendered');
    require("../../embed.js");
    var event = await pending;

    expect(event.detail.count).toBe(0);
    expect(event.detail.element).toBe(document.getElementById('isso-thread'));
    expect(event.detail.error).toBeUndefined();
  });

  test('fires with count 0 and the error detail when the fetch fails', async () => {
    var { api } = setupEmbed();
    api.fetch.mockRejectedValue("Internal Server Error");

    var pending = waitForEvent('isso-thread-rendered');
    require("../../embed.js");
    var event = await pending;

    expect(event.detail.count).toBe(0);
    expect(event.detail.error).toBe("Internal Server Error");
  });
});
