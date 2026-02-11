export default {
  server: {
    port: 2720,
    allowedHosts: ["tower.tail790bbc.ts.net"],
    proxy: {
      "/api": "http://localhost:2721",
    },
  },
};
