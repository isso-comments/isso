// https://stackoverflow.com/questions/56261381/how-do-i-set-a-timezone-in-my-jest-config/56482581#56482581
// Requires global-setup.js

test('Timezones should always be UTC', () => {
    expect(new Date().getTimezoneOffset()).toBe(0);
});
