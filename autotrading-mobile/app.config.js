export default ({ config }) => ({
  ...config,
  extra: {
    apiBase: process.env.API_BASE || "http://localhost:8000",
  },
});
