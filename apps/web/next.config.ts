import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Shared workspace types are shipped as TS source, so Next must transpile them.
  transpilePackages: ['@throughline/shared'],
};

export default nextConfig;
