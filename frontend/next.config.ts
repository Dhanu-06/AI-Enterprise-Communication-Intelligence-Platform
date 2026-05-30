import type { NextConfig } from "next";
import path from "path";

const backendInternalUrl =
  process.env.BACKEND_INTERNAL_URL || "http://localhost:8000";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  output: "standalone",
  outputFileTracingRoot: path.join(__dirname),
  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${backendInternalUrl}/api/v1/:path*`,
      },
    ];
  },
};

export default nextConfig;
