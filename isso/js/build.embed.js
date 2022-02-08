({
    baseUrl: ".",
    mainConfigFile: 'config.js',
    stubModules: ['text', 'jade'],

    name: "../../node_modules/almond/almond",
    include: ['embed'],
    out: "embed.min.js",

    optimizeAllPluginResources: true,
    wrap: true
})
