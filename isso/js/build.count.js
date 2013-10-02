({
    baseUrl: ".",
    mainConfigFile: 'config.js',
    paths: {
        "app/text/svg": "app/text/dummy"
    },

    name: "components/almond/almond",
    include: ['count'],
    out: "count.min.js",
    wrap: true
})
