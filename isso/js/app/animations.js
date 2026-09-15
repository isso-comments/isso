"use strict";

var config = require("app/config");

// Animation timing constants

// Default timeout for animation completion fallback in milliseconds. This is used when:
// 1. The computed animation duration cannot be read from the element
// 2. The animation duration is 0s or invalid
var DEFAULT_ANIMATION_TIMEOUT_MS = 500;

// Additional buffer time added to the computed animation duration to ensure
// the animation completes before the callback is triggered
var ANIMATION_BUFFER_MS = 200;

// Interval for checking scroll position stability
var SCROLL_CHECK_INTERVAL_MS = 50;

// Maximum time to wait for scroll completion before forcing callback
var SCROLL_COMPLETION_TIMEOUT_MS = 2000;

/**
 * Unwrap a DOM element if it's wrapped in our Element class
 * @param {Element|HTMLElement} element - Either a wrapped Element or raw DOM element
 * @returns {HTMLElement} - Raw DOM element
 */
var unwrap = function(element) {
    // Check if it's our wrapped Element class (has .obj property)
    if (element && typeof element === 'object' && element.obj instanceof window.Element) {
        return element.obj;
    }
    // Already a raw DOM element or null
    return element;
};

/**
 * Check if animations are enabled based on config and user preferences
 * @returns {boolean}
 */
var isEnabled = function() {
    // Check if animations are disabled in config
    if (config["animations"] === false) {
        return false;
    }

    // Check if user prefers reduced motion
    if (window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        return false;
    }

    return true;
};

/**
 * Animate element insertion with fade-in effect
 * @param {Element|HTMLElement} element - The DOM element to animate (wrapped or raw)
 * @param {boolean} scrollIntoView - Whether to scroll to the element
 */
var animateInsert = function(element, scrollIntoView) {
    var rawElement = unwrap(element);

    if (!isEnabled()) {
        if (scrollIntoView) {
            scrollToElement(rawElement);
        }
        return;
    }

    // Function to add animation class
    var addAnimation = function() {
        // Remove initial state and add animation class
        rawElement.classList.remove('isso-anim-initial');
        rawElement.classList.add('isso-anim-in');

        // Remove animation class after animation completes
        var handleAnimationEnd = function() {
            rawElement.classList.remove('isso-anim-in');
            rawElement.removeEventListener('animationend', handleAnimationEnd);
        };

        rawElement.addEventListener('animationend', handleAnimationEnd);
    };

    requestAnimationFrame(function() {
        if (scrollIntoView) {
            // Wait for scroll to complete before animating
            scrollToElement(rawElement, function() {
                addAnimation();
            });
        } else {
            addAnimation();
        }
    });
};

/**
 * Prepare and insert element with animation
 * This is a convenience function that handles the complete animation workflow:
 * 1. Prepares the element for animation (adds initial state)
 * 2. Appends element to parent
 * 3. Triggers the animation
 *
 * @param {Element|HTMLElement} element - The DOM element to animate (wrapped or raw)
 * @param {Element|HTMLElement} parent - The parent element to append to (wrapped or raw)
 * @param {boolean} scrollIntoView - Whether to scroll to the element
 */
var insertWithAnimation = function(element, parent, scrollIntoView) {
    var rawElement = unwrap(element);
    var rawParent = unwrap(parent);

    if (isEnabled()) {
        // Set initial state before element is visible
        rawElement.classList.add('isso-anim-initial');
    }

    // Append to parent
    rawParent.appendChild(rawElement);

    // Trigger animation
    animateInsert(rawElement, scrollIntoView);
};

/**
 * Animate element removal with fade-out effect
 * @param {Element|HTMLElement} element - The DOM element to animate (wrapped or raw)
 * @param {Function} callback - Function to call after animation completes
 */
var animateRemove = function(element, callback) {
    var rawElement = unwrap(element);

    if (!isEnabled()) {
        if (callback) {
            callback();
        }
        return;
    }

    // Add animation class
    rawElement.classList.add('isso-anim-out');

    var completed = false;
    var timeoutId = null;

    // Wait for animation to complete before removing
    var handleAnimationEnd = function() {
        if (completed) return;
        completed = true;

        // Clear the fallback timeout
        if (timeoutId !== null) {
            clearTimeout(timeoutId);
        }

        rawElement.removeEventListener('animationend', handleAnimationEnd);
        if (callback) {
            callback();
        }
    };

    rawElement.addEventListener('animationend', handleAnimationEnd);

    // Get animation duration from computed style for fallback timeout
    var fallbackTimeout = DEFAULT_ANIMATION_TIMEOUT_MS;
    try {
        var style = window.getComputedStyle(rawElement);
        var durationStr = style.animationDuration;
        if (durationStr && durationStr !== '0s') {
            // Parse duration (could be in 's' or 'ms')
            var duration = parseFloat(durationStr);
            // Validate that duration is a valid number
            if (!isNaN(duration) && duration > 0) {
                fallbackTimeout = durationStr.includes('ms') ? duration : duration * 1000;
                // Add buffer to ensure animation completes
                fallbackTimeout += ANIMATION_BUFFER_MS;
            }
        }
    } catch (e) {
        // If we can't read the style, use default fallback timeout
    }

    // Fallback timeout in case animationend doesn't fire
    timeoutId = setTimeout(function() {
        handleAnimationEnd();
    }, fallbackTimeout);
};

/**
 * Creates a self-cancelling scroll completion watcher.
 * Polls window.scrollY every 50ms and fires the callback once
 * the position has been stable for one tick, or after a 2s safety timeout.
 *
 * @param {Function} callback - Called once when scrolling is deemed complete
 * @returns {void}
 */
var watchScrollCompletion = function(callback) {
    var called = false;
    var lastScrollY = window.scrollY;
    var scrollCheckInterval = null;
    var fallbackTimeout = null;

    // Single exit point — clears both the interval and timeout
    // before invoking the callback, preventing double invocation
    var done = function() {
        if (called) return;
        called = true;
        if (scrollCheckInterval !== null) {
            clearInterval(scrollCheckInterval);
        }
        if (fallbackTimeout !== null) {
            clearTimeout(fallbackTimeout);
        }
        callback();
    };

    // Poll at regular intervals — the initial delay naturally ensures the first
    // check happens after scrollIntoView has had a chance to begin moving
    scrollCheckInterval = setInterval(function() {
        if (window.scrollY === lastScrollY) {
            done();
        }
        lastScrollY = window.scrollY;
    }, SCROLL_CHECK_INTERVAL_MS);

    // Safety net: if scroll detection stalls (e.g. very long page,
    // slow device, or reduced-motion override), force-complete after timeout
    fallbackTimeout = setTimeout(done, SCROLL_COMPLETION_TIMEOUT_MS);
};

/**
 * Smooth scrolls to a given element with an optional post-scroll callback.
 * Falls back to instant scroll on browsers that don't support smooth behavior.
 *
 * @param {Element|HTMLElement} element - The target DOM element to scroll to (wrapped or raw)
 * @param {Function} callback - Optional. Called after scroll completes (or immediately on fallback)
 */
var scrollToElement = function(element, callback) {
    var rawElement = unwrap(element);

    if (!rawElement) {
        return;
    }

    // Smooth scroll path — supported in all modern browsers
    if ('scrollBehavior' in document.documentElement.style) {
        try {
            rawElement.scrollIntoView({ behavior: 'smooth' });

            // Only watch for completion if a callback was provided
            if (callback) {
                watchScrollCompletion(callback);
            }
            return;
        } catch (e) {
            // scrollIntoView with options not supported — fall through to basic scroll
        }
    }

    // Fallback: instant scroll, no completion detection needed
    rawElement.scrollIntoView();

    // Instant scroll, so callback can be called immediately
    if (callback) {
        requestAnimationFrame(callback);
    }
};

module.exports = {
    isEnabled: isEnabled,
    insertWithAnimation: insertWithAnimation,
    animateRemove: animateRemove,
    scrollToElement: scrollToElement
};