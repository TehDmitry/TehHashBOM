module.exports = {
    filenameHashing: false,
    outputDir: "../Scripts/TehHashBOM/resources/vue/",

    publicPath: process.env.NODE_ENV === "production" ? "./" : "/",

    configureWebpack: (config) => {
        if (process.env.NODE_ENV === "production") {
            config.output.filename = "js/[name].min.js";
            config.output.chunkFilename = "js/[name].min.js";
        } else {
            config.output.filename = "js/[name].js";
            config.output.chunkFilename = "js/[name].js";
        }
    },

    transpileDependencies: ["vuetify"],
};
