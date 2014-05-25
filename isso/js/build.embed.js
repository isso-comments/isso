({
    baseUrl: ".",
    mainConfigFile: 'config.js',
    stubModules: ['text'],

    name: "components/almond/almond",
    include: ['embed'],
    out: "embed.min.js",

    optimizeAllPluginResources: true,
    wrap: true
})
