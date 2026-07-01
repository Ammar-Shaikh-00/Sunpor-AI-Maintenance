module.exports = {
  input: [
    "src/**/*.{js,jsx,ts,tsx}"
  ],
  output: "./src/locales",
  options: {
    debug: false,
    removeUnusedKeys: true,
    func: {
      list: ["t"],
      extensions: [".js", ".jsx"]
    },
    lngs: ["de"],
    defaultLng: "de",
    resource: {
      loadPath: "src/locales/{{lng}}.json",
      savePath: "src/locales/{{lng}}.json"
    }
  }
};
