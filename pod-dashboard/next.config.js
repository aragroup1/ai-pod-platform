/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  env: {
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://backend-production-7aae.up.railway.app/api/v1',
  },
  // Force a rebuild by adding a timestamp
  generateBuildId: async () => {
    return `build-${Date.now()}`
  },
}

module.exports = nextConfig
