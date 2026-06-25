/** @type {import('next').NextConfig} */
const apiOrigin = process.env.AEGISAI_API_ORIGIN ?? "http://127.0.0.1:8000";

const nextConfig = {
  output: "standalone",
  poweredByHeader: false,
  compress: true,
  reactStrictMode: true,
  async rewrites() {
    return [
      { source: "/health", destination: `${apiOrigin}/health` },
      { source: "/api/:path*", destination: `${apiOrigin}/api/:path*` }
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
          {
            key: "Content-Security-Policy",
            value:
              "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self' data:; connect-src 'self' http://localhost:8000 http://127.0.0.1:8000 https:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"
          }
        ]
      }
    ];
  }
};

export default nextConfig;
