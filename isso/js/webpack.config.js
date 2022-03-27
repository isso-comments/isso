const path = require('path');
/* Needed for LimitChunkCountPlugin */
const webpack = require('webpack');

module.exports = [
    {
        name: "dev",
        entry: {
            embed: path.resolve(__dirname, 'embed.js'),
            count: path.resolve(__dirname, 'count.js'),
        },
        /* https://webpack.js.org/configuration/mode/
         * Available modes: development, production, none
         */
        mode: 'development',
        /* https://webpack.js.org/configuration/devtool/ */
        devtool: 'source-map',
        /* Instruct webpack to emit ES5-compatible syntax for not-so-recent (pre-2017) browsers
         * Note: Both 'web' and 'es5' are needed!
         * https://webpack.js.org/configuration/target/ */
        target: ['web', 'es5'],
        /* https://webpack.js.org/configuration/resolve/#resolvemodules */
        resolve: {
            /* Allow omission of `isso/js` path */
            modules: [
                path.resolve(__dirname), // resolves to webpack.config.js file location
                'node_modules',
            ],
        },
        plugins: [
            /* Disable splitting *.(dev|min).js into multiple chunked js files
             * https://stackoverflow.com/questions/62048737/how-do-i-disable-webpack-4-code-splitting#62092571 */
            new webpack.optimize.LimitChunkCountPlugin({
                maxChunks: 1,
            }),
        ],
        /* https://webpack.js.org/guides/asset-modules/ */
        module: {
          rules: [
            {
             /* Read raw file contents when `require`-ing .svg files */
             test: /\.svg/,
             type: 'asset/source'
            },
          ],
        },
        /* https://webpack.js.org/concepts/output/ */
        output: {
            filename: '[name].dev.js',
            path: path.resolve(__dirname),
            //clean: true, // what does this do?
        },
    },
    {
        name: "prod",
        // https://webpack.js.org/configuration/configuration-types/#dependencies
        dependencies: ["dev",],
        mode: 'production',
        optimization: {
            /* Tree shaking
             * https://webpack.js.org/guides/tree-shaking/ */
            usedExports: true,
            // sideEffects=true, evaluates package.json sideEffects of inherited
            // modules for tree-shaking of unused imports
            // on by default for prod builds
            //sideEffects: true,
        },
        devtool: false, // no eval or source maps in prod
        output: {
            filename: '[name].min.js',
            path: path.resolve(__dirname),
        }
    },
];
// https://webpack.js.org/configuration/configuration-types/#parallelism
module.exports.parallelism = 4;
