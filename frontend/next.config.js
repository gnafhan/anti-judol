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
  // Webpack configuration for path aliases
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'lib': path.resolve(__dirname, 'src/lib'),
      'components': path.resolve(__dirname, 'src/components'),
      'hooks': path.resolve(__dirname, 'src/hooks'),
      'utils': path.resolve(__dirname, 'src/utils'),
      'types': path.resolve(__dirname, 'src/types'),
      'variables': path.resolve(__dirname, 'src/variables'),
    };
    return config;
  },
};

module.exports = nextConfig;
