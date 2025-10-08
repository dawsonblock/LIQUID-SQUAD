/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  output: 'standalone', // Enable standalone output for Docker deployment
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  async rewrites() {
    return [
      {
        source: '/api/proxy/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/:path*`,
      },
    ];
  },
  webpack: (config, { isServer, dev }) => {
    if (!dev) {
      // Ensure optimization object exists
      config.optimization = config.optimization || {};
      // Explicitly enable minimization for production builds if needed,
      // though it's default. This is safer than replacing the object.
      config.optimization.minimize = true;
    }
    return config;
  },
};

module.exports = nextConfig;
