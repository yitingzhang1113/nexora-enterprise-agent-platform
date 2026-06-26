/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  async redirects() {
    // 兼容旧版缓存里的死链 (历史版本曾用 connectors/configuration 路由)
    return [
      { source: "/admin/connectors", destination: "/admin/documents", permanent: false },
      { source: "/admin/configuration", destination: "/admin/status", permanent: false },
    ];
  },
};

module.exports = nextConfig;
