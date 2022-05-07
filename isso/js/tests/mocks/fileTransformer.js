// https://jestjs.io/docs/next/code-transformation#transforming-images-to-their-path

const path = require('path');

module.exports = {
  process(sourceText, sourcePath, options) {
    return {
      code: `module.exports = ${JSON.stringify(path.basename(sourcePath))};`,
    };
  },
};
