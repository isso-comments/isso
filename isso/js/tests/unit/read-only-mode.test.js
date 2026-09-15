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
            '<script src="http://isso.api/js/embed.min.js" data-isso="/"></script>';
    });

    afterEach(() => {
        // Drop any cookies a test set so they don't leak into the next one.
        document.cookie.split(";").forEach((c) => {
            document.cookie = c.replace(/=.*/, "=;expires=Thu, 01 Jan 1970 00:00:00 GMT");
        });
    });

    test('should not render postbox when the server marks the thread read-only', () => {
        jest.doMock('app/count', () => jest.fn());
        jest.doMock('app/api', () => ({
            endpoint: "/",
            feed: () => "/feed",
            config: () => ({ then: (ok) => ok({ config: {} }) }),
            fetch: () => ({ then: (ok) => ok({ total_replies: 0, replies: [], "read-only": true }) }),
        }));

        const $ = require("app/dom");
        require("embed");

        expect($('.isso-postbox')).toBeNull();
    });

    test('should render postbox when the server marks the thread writable', () => {
        jest.doMock('app/count', () => jest.fn());
        jest.doMock('app/api', () => ({
            endpoint: "/",
            feed: () => "/feed",
            config: () => ({ then: (ok) => ok({ config: {} }) }),
            fetch: () => ({ then: (ok) => ok({ total_replies: 0, replies: [], "read-only": false }) }),
        }));

        const $ = require("app/dom");
        require("embed");

        expect($('.isso-postbox')).not.toBeNull();
    });

    test('should not render reply, edit, and delete buttons in read-only mode', () => {
        const isso = require("app/isso");
        const $ = require("app/dom");
        const config = require("app/config");
        const template = require("app/template");
        const i18n = require("app/i18n");
        const svg = require("app/svg");

        // The read-only flag is set at runtime from the comment-fetch (GET /)
        // response (see embed.js); simulate that state here.
        config["read-only"] = true;

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

    test('should not throw when rendering an own comment in read-only mode with reply-to-self disabled', () => {
        const isso = require("app/isso");
        const $ = require("app/dom");
        const config = require("app/config");
        const template = require("app/template");
        const i18n = require("app/i18n");
        const svg = require("app/svg");

        config["read-only"] = true;
        config["reply-to-self"] = false;

        // The delayed reply-link handling triggers only when the browser holds
        // an isso-<id> cookie for the comment (i.e. the visitor authored it).
        document.cookie = "isso-1=deadbeef";

        template.set("conf", config);
        template.set("i18n", i18n.translate);
        template.set("pluralize", i18n.pluralize);
        template.set("svg", svg);

        let isso_thread = $('#isso-thread');
        isso_thread.append('<div id="isso-root"></div>');

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

        expect(() => {
            isso.insert({comment, scrollIntoView: false, offset: 0});
        }).not.toThrow();

        expect($('a.isso-reply')).toBeNull();
    });
});
