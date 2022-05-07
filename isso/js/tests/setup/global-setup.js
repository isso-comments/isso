// https://stackoverflow.com/questions/56261381/how-do-i-set-a-timezone-in-my-jest-config/56482581#56482581
module.exports = async () => {
    process.env.TZ = 'UTC';
};
