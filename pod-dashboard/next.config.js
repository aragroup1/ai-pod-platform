/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Force this environment variable into the build
  env: {
    NEXT_PUBLIC_API_URL: 'https://backend-production-7aae.up.railway.app/api/v1',
  },
  // Disable Next.js caching during build
  generateBuildId: async () => {
    // Use timestamp to force new build ID
    return `build-${new Date().getTime()}`
  },
}

module.exports = nextConfig
