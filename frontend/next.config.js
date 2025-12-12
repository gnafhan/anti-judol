/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH,
  assetPrefix: process.env.NEXT_PUBLIC_BASE_PATH,
  images: {
    domains: [
      'images.unsplash.com',
      'i.ibb.co',
      'scontent.fotp8-1.fna.fbcdn.net',
      'yt3.ggpht.com',
      'i.ytimg.com',
    ],
    unoptimized: true,
  },
  // Enable standalone output for Docker
  output: 'standalone',
  // Webpack configuration for path aliases - must match tsconfig baseUrl: "src"
  webpack: (config) => {
    // Add src directory to module resolution
    config.resolve.modules = [
      path.resolve(__dirname, 'src'),
      'node_modules',
      ...(config.resolve.modules || []),
    ];
    return config;
  },
};

module.exports = nextConfig;
