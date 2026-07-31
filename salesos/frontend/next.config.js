/** @type {import('next').NextConfig} */
const nextConfig = {

  output: "standalone",
  images: {
    domains: ["localhost"],
    formats: ["image/avif", "image/webp"],
  },
  experimental: {
    optimizePackageImports: [
      "lucide-react",
      "recharts",
      "@radix-ui/react-avatar",
      "@radix-ui/react-dialog",
      "@radix-ui/react-dropdown-menu",
      "@radix-ui/react-select",
      "@radix-ui/react-tabs",
      "@radix-ui/react-toast",
      "@radix-ui/react-tooltip",
      "@tanstack/react-table",
      "@tanstack/react-query",
      "class-variance-authority",
      "tailwind-merge",
    ],
  },
  compiler: {
    removeConsole: process.env.NODE_ENV === "production" ? { exclude: ["error", "warn"] } : false,
  },
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/:path*`,
      },
    ];
  },
  webpack: (config, { isServer }) => {
    if (!isServer) {
      config.optimization.splitChunks = {
        chunks: 'all',
        maxInitialRequests: 25,
        minSize: 20000,
        cacheGroups: {
          framework: {
            test: /[\\/]node_modules[\\/](react|react-dom|next)[\\/]/,
            name: 'framework',
            chunks: 'all',
            priority: 40,
          },
          radix: {
            test: /[\\/]node_modules[\\/]@radix-ui[\\/]/,
            name: 'vendor-radix',
            chunks: 'all',
            priority: 30,
          },
          charts: {
            test: /[\\/]node_modules[\\/](recharts|d3|victory)[\\/]/,
            name: 'vendor-charts',
            chunks: 'all',
            priority: 20,
          },
          commons: {
            test: /[\\/]node_modules[\\/](axios|zod|clsx|class-variance-authority|tailwind-merge)[\\/]/,
            name: 'vendor-commons',
            chunks: 'all',
            priority: 10,
          },
        },
      };
    }
    return config;
  },
};

module.exports = nextConfig;
