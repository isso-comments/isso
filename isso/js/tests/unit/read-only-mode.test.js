/**
 * @jest-environment jsdom
 */

"use strict";

describe('Isso read-only mode', () => {
    beforeEach(() => {
        jest.resetModules();

        // globals.offset.localTime() will be passed to i18n.ago()
        // localTime param will then be called as localTime.getTime()
        jest.mock('app/globals', () => ({
            offset: {
                localTime: jest.fn(() => ({
                    getTime: jest.fn(() => 0),
                })),
            },
        }));

        document.body.innerHTML =
            '<div id="isso-thread"></div>' +
            '<script src="http://isso.api/js/embed.min.js"' +
            ' data-isso="/"' +
            ' data-isso-read-only="true"></script>';
    });

    test('should not render postbox in read-only mode', () => {
        const $ = require("app/dom");
        const config = require("app/config");
        const template = require("app/template");
        const i18n = require("app/i18n");
        const svg = require("app/svg");

        template.set("conf", config);
        template.set("i18n", i18n.translate);
        template.set("pluralize", i18n.pluralize);
        template.set("svg", svg);

        let isso_thread = $('#isso-thread');
        isso_thread.append('<div id="isso-root"></div>');

        expect($('.isso-postbox')).toBeNull();
    });

    test('should not render reply, edit, and delete buttons in read-only mode', () => {
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

        let isso_thread = $('#isso-thread');
        isso_thread.append('<div id="isso-root"></div>');

        // Simulate a comment object
        let comment = {
            id: 1,
            hash: "abc123",
            author: "TestUser",
            website: null,
            created: 1651788192.4473603,
            mode: 1,
            text: "Test comment",
            likes: 0,
            dislikes: 0,
            replies: [],
            hidden_replies: 0,
            parent: null
        };

        // Render comment
        isso.insert({comment, scrollIntoView: false, offset: 0});

        // Verify that interactive buttons are not rendered in read-only mode
        expect($('a.isso-reply')).toBeNull();
        expect($('a.isso-edit')).toBeNull();
        expect($('a.isso-delete')).toBeNull();
    });
});
