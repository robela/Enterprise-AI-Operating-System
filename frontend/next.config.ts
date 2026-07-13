import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  reactStrictMode: true,
  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**",
      },
    ],
  },
  rewrites: async () => {
    // Use environment variable set at build or deployment time
    // If not available, API routes will handle proxying
    return [];
  },
};

export default nextConfig;
