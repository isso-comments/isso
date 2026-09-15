/**
 * @jest-environment jsdom
 */

describe('Animation Module', () => {
    beforeEach(() => {
        document.body.innerHTML = '<div id="test-element"></div><div id="parent-element"></div>';

        // Mock matchMedia
        Object.defineProperty(window, 'matchMedia', {
            writable: true,
            value: jest.fn().mockImplementation(query => ({
                matches: false,
                media: query,
                onchange: null,
                addListener: jest.fn(),
                removeListener: jest.fn(),
                addEventListener: jest.fn(),
                removeEventListener: jest.fn(),
                dispatchEvent: jest.fn(),
            })),
        });

        // Mock requestAnimationFrame
        global.requestAnimationFrame = jest.fn((cb) => {
            cb();
            return 1;
        });

        // Mock scrollY
        Object.defineProperty(window, 'scrollY', {
            writable: true,
            value: 0
        });

        // Mock scrollBehavior support
        Object.defineProperty(document.documentElement.style, 'scrollBehavior', {
            writable: true,
            value: ''
        });

        jest.useFakeTimers();
    });

    afterEach(() => {
        jest.clearAllMocks();
        jest.useRealTimers();
    });

    describe('with animations enabled', () => {
        let animations;

        beforeEach(() => {
            jest.resetModules();
            jest.doMock("app/config", () => ({
                animations: true
            }));
            animations = require("app/animations");
        });

        test('isEnabled returns true when animations are enabled', () => {
            expect(animations.isEnabled()).toBe(true);
        });

        test('isEnabled respects prefers-reduced-motion', () => {
            window.matchMedia = jest.fn().mockImplementation(query => ({
                matches: query === '(prefers-reduced-motion: reduce)',
                media: query,
            }));

            expect(animations.isEnabled()).toBe(false);
        });

        test('insertWithAnimation adds element to parent with animation', () => {
            const element = document.getElementById('test-element');
            const parent = document.getElementById('parent-element');

            // Remove element from DOM first
            element.remove();

            animations.insertWithAnimation(element, parent, false);

            // Check element was appended to parent
            expect(parent.contains(element)).toBe(true);

            // Check initial animation class was added
            expect(element.classList.contains('isso-anim-initial')).toBe(true);

            // Advance timers to trigger requestAnimationFrame
            jest.runAllTimers();

            // Check animation class was added
            expect(element.classList.contains('isso-anim-in')).toBe(true);
        });

        test('insertWithAnimation handles scrollIntoView', () => {
            const element = document.getElementById('test-element');
            const parent = document.getElementById('parent-element');

            element.remove();
            element.scrollIntoView = jest.fn();

            animations.insertWithAnimation(element, parent, true);

            // Advance timers to trigger requestAnimationFrame and scroll
            jest.runAllTimers();

            expect(element.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
        });

        test('insertWithAnimation removes animation classes after completion', () => {
            const element = document.getElementById('test-element');
            const parent = document.getElementById('parent-element');

            element.remove();

            animations.insertWithAnimation(element, parent, false);

            // Advance timers to trigger animation
            jest.runAllTimers();

            expect(element.classList.contains('isso-anim-in')).toBe(true);

            // Simulate animationend event
            const event = new Event('animationend');
            element.dispatchEvent(event);

            expect(element.classList.contains('isso-anim-in')).toBe(false);
        });

        test('insertWithAnimation with scroll waits for scroll completion before animating', () => {
            const element = document.getElementById('test-element');
            const parent = document.getElementById('parent-element');

            element.remove();
            element.scrollIntoView = jest.fn();

            animations.insertWithAnimation(element, parent, true);

            // Element should be in parent and have initial class
            expect(parent.contains(element)).toBe(true);
            expect(element.classList.contains('isso-anim-initial')).toBe(true);

            // Advance to trigger requestAnimationFrame
            jest.runAllTimers();

            // Should have called scrollIntoView
            expect(element.scrollIntoView).toHaveBeenCalled();

            // Animation class should be added after scroll completion
            expect(element.classList.contains('isso-anim-in')).toBe(true);
        });

        test('animateRemove adds animation class and calls callback', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            animations.animateRemove(element, callback);

            expect(element.classList.contains('isso-anim-out')).toBe(true);

            // Simulate animationend event
            const event = new Event('animationend');
            element.dispatchEvent(event);

            expect(callback).toHaveBeenCalled();
        });

        test('animateRemove has fallback timeout', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            animations.animateRemove(element, callback);

            expect(element.classList.contains('isso-anim-out')).toBe(true);

            // Don't fire animationend, just advance timers
            jest.advanceTimersByTime(500);

            expect(callback).toHaveBeenCalled();
        });

        test('animateRemove prevents double callback execution', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            animations.animateRemove(element, callback);

            // Fire animationend event
            const event = new Event('animationend');
            element.dispatchEvent(event);

            // Also trigger timeout
            jest.advanceTimersByTime(500);

            // Callback should only be called once
            expect(callback).toHaveBeenCalledTimes(1);
        });

        test('scrollToElement uses smooth scrollIntoView when available', () => {
            const element = document.getElementById('test-element');
            element.scrollIntoView = jest.fn();

            animations.scrollToElement(element);

            expect(element.scrollIntoView).toHaveBeenCalledWith({
                behavior: 'smooth'
            });
        });

        test('scrollToElement calls callback after scroll completion', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();
            element.scrollIntoView = jest.fn();

            animations.scrollToElement(element, callback);

            expect(element.scrollIntoView).toHaveBeenCalledWith({
                behavior: 'smooth'
            });

            // Simulate scroll completion by advancing timers
            // First tick is skipped, second tick detects stable position
            jest.advanceTimersByTime(50); // First tick
            jest.advanceTimersByTime(50); // Second tick - should detect stable

            expect(callback).toHaveBeenCalled();
        });

        test('scrollToElement callback has safety timeout', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();
            element.scrollIntoView = jest.fn();

            // Simulate continuous scrolling by changing scrollY
            let mockScrollYCounter = 0;
            Object.defineProperty(window, 'scrollY', {
                get: () => mockScrollYCounter++,
                configurable: true
            });

            animations.scrollToElement(element, callback);

            // Advance to safety timeout
            jest.advanceTimersByTime(2000);

            expect(callback).toHaveBeenCalled();
        });

        test('scrollToElement falls back when scrollBehavior is not supported', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            // Create a new style object without scrollBehavior
            const mockStyle = {};
            Object.defineProperty(document.documentElement, 'style', {
                configurable: true,
                value: mockStyle
            });

            element.scrollIntoView = jest.fn();

            animations.scrollToElement(element, callback);

            // Should call basic scrollIntoView without options
            expect(element.scrollIntoView).toHaveBeenCalledWith();

            // Callback should be called immediately
            jest.runAllTimers();
            expect(callback).toHaveBeenCalled();
        });

        test('scrollToElement handles scrollIntoView exception', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            // Mock to throw only when called with options (smooth scroll)
            // but succeed when called without options (fallback)
            element.scrollIntoView = jest.fn((options) => {
                if (options && options.behavior === 'smooth') {
                    throw new Error('Not supported');
                }
                // Fallback call without options succeeds silently
            });

            animations.scrollToElement(element, callback);

            // Should have been called twice: once with options (threw), once without (succeeded)
            expect(element.scrollIntoView).toHaveBeenCalledTimes(2);
            expect(element.scrollIntoView).toHaveBeenCalledWith({ behavior: 'smooth' });
            expect(element.scrollIntoView).toHaveBeenCalledWith();

            // Callback should be called immediately after fallback
            jest.runAllTimers();
            expect(callback).toHaveBeenCalled();
        });

        test('scrollToElement handles null element gracefully', () => {
            expect(() => {
                animations.scrollToElement(null);
            }).not.toThrow();
        });
    });

    describe('with animations disabled', () => {
        let animations;

        beforeEach(() => {
            jest.resetModules();
            jest.doMock("app/config", () => ({
                animations: false
            }));
            animations = require("app/animations");
        });

        test('isEnabled returns false when config.animations is false', () => {
            expect(animations.isEnabled()).toBe(false);
        });

        test('insertWithAnimation skips animation when disabled', () => {
            const element = document.getElementById('test-element');
            const parent = document.getElementById('parent-element');

            element.remove();

            animations.insertWithAnimation(element, parent, false);

            expect(parent.contains(element)).toBe(true);
            expect(element.classList.contains('isso-anim-initial')).toBe(false);
            expect(element.classList.contains('isso-anim-in')).toBe(false);
        });

        test('animateRemove calls callback immediately when disabled', () => {
            const element = document.getElementById('test-element');
            const callback = jest.fn();

            animations.animateRemove(element, callback);

            expect(element.classList.contains('isso-anim-out')).toBe(false);
            expect(callback).toHaveBeenCalled();
        });
    });
});