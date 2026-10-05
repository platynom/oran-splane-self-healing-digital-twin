import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: process.env.NEXT_OUTPUT === "standalone" ? "standalone" : undefined,
  outputFileTracingIncludes: { "/**": ["./node_modules/.prisma/client/**"] },
  // The simulator at / absorbs the former pages; old links land on the matching diagram state (query strings pass through).
  async redirects() {
    return [
      { source: "/learn", destination: "/?panel=lessons", permanent: false },
      { source: "/learn/:lessonId", destination: "/?panel=lesson%3A:lessonId", permanent: false },
      { source: "/replay", destination: "/?level=3", permanent: false },
      { source: "/sandbox", destination: "/?level=4&focus=recovery-loop&panel=sandbox", permanent: false },
      { source: "/dashboard", destination: "/?results=1", permanent: false },
      { source: "/catalogue", destination: "/?focus=hw-faults&panel=catalogue", permanent: false },
    ];
  },
  async headers() {
    return [
      {
        source: "/(.*)",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Frame-Options", value: "DENY" },
        ],
      },
    ];
  },
};

export default nextConfig;
