/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 * https://jestjs.io/docs/configuration#testenvironmentoptions-object
 */

"use strict";

/*
 * Test goals:
 * - Test editorify()
 * - Test insert()
 * - Test insert_loader()
 * - Test Postbox()
 * Also, untangle Postbox functions from DOM element
 */

test('Editorify text area', () => {
  // Set up our document body
  document.body.innerHTML =
    '<div id=isso-thread></div>' +
    // Note: `src` and `data-isso` need to be set,
    // else `api` fails to initialize!
    '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';

  let placeholder = 'Type here'
  let html = "<div class='isso-textarea isso-placeholder' contenteditable='true'>Type here</div>"

  jest.mock('app/i18n', () => ({
    translate: jest.fn(key => placeholder),
  }));

  const isso = require("app/isso");
  const $ = require("app/dom");

  var textarea = $.htmlify(html);
  var isso_thread = $('#isso-thread');
  isso_thread.append(textarea);
  let area = document.querySelectorAll('.isso-textarea')[0];

  isso.editorify(textarea);
  expect(textarea.getAttribute('contentEditable')).toBe('true');

  // textarea.focus() does not work here,
  // Maybe some JSDOM oddities prevent addEventListener()?
  area.dispatchEvent(new window.MouseEvent('focus'));

  // classList returns {'0': 'class1, '1': 'class2', ...}
  expect(textarea.innerHTML).toBe("");
  expect(Object.values(textarea.classList)).not.toContain("isso-placeholder");

  // textarea.blur() does not work here
  area.dispatchEvent(new window.MouseEvent('blur'));

  expect(Object.values(textarea.classList)).toContain("isso-placeholder");
  expect(textarea.innerHTML).toBe("Type here");
});
