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

test('data-isso-* attributes should override i18n strings', () => {
  // Set up our document body
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"'
          + 'data-isso-lang="de"'
          + 'data-isso-postbox-text-text-de="Kommentiere hier, Alter!"'
          + '</script>';

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
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-textarea').placeholder).toMatch('Kommentiere hier, Alter!');
});

test('data-isso-* i18n strings should be accepted with dashes', () => {
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"></script>';

  var script_tag = document.getElementsByTagName('script')[0];
  script_tag.setAttributeNS(null, 'data-isso-lang', 'pt_BR');
  script_tag.setAttributeNS(null, 'data-isso-postbox-text-text-pt-br', 'Digite seu comentário.');

  expect(script_tag.getAttribute('data-isso-lang')).toBe('pt_BR');
  // expect(script_tag).toBe('')

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
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-textarea').placeholder).toMatch('Digite seu comentário.');
});

test('data-isso-* i18n strings should be accepted with underscores', () => {
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js"'
          + 'data-isso="/"></script>';

  var script_tag = document.getElementsByTagName('script')[0];
  script_tag.setAttributeNS(null, 'data-isso-lang', 'pt_br');
  script_tag.setAttributeNS(null, 'data-isso-postbox-text-text-pt_BR', 'Digite seu comentário.');

  expect(script_tag.getAttribute('data-isso-lang')).toBe('pt_br');

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
  isso_thread.append(new isso.Postbox(null));

  expect($('.isso-textarea').placeholder).toMatch('Digite seu comentário.');
});
