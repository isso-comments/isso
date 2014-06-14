({
    baseUrl: ".",
    mainConfigFile: 'config.js',
    stubModules: ['text', 'jade'],

    name: "components/almond/almond",
    include: ['embed'],
    out: "embed.min.js",

    optimizeAllPluginResources: true,
    wrap: true
})
