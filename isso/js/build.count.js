({
    baseUrl: ".",
    mainConfigFile: 'config.js',
    paths: {
        "app/text/svg": "app/text/dummy",
        "app/text/css": "app/text/dummy"
    },

    name: "../../node_modules/almond/almond",
    include: ['count'],
    out: "count.min.js",
    wrap: true
})
