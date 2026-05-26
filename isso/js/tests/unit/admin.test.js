/**
 * @jest-environment jsdom
 */

/* Keep the above exactly as-is!
 * https://jestjs.io/docs/configuration#testenvironment-string
 */

const { setCountBadge } = require("admin");

describe("setCountBadge", () => {
    test("sets count to given value", () => {
        document.body.innerHTML = `<span id="count-mode-1">Valid (<span class="count">3</span>)</span>`;
        setCountBadge("count-mode-1", 7);
        expect(document.getElementById("count-mode-1").querySelector('.count').textContent).toBe("7");
    });

    test("sets count to zero", () => {
        document.body.innerHTML = `<span id="count-mode-2">Pending (<span class="count">5</span>)</span>`;
        setCountBadge("count-mode-2", 0);
        expect(document.getElementById("count-mode-2").querySelector('.count').textContent).toBe("0");
    });

    test("does nothing when count span is absent", () => {
        document.body.innerHTML = `<span id="count-mode-2">Pending (3)</span>`;
        expect(() => setCountBadge("count-mode-2", 5)).not.toThrow();
        expect(document.getElementById("count-mode-2").textContent).toBe("Pending (3)");
    });

    test("does nothing for a nonexistent element", () => {
        document.body.innerHTML = "";
        expect(() => setCountBadge("count-mode-99", 1)).not.toThrow();
    });
});
