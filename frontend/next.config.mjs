/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Static export: `next build` emits a fully static site to `out/`, which the
  // FastAPI backend serves in the unified single-container deployment.
  output: "export",
  images: {
    // Required for static export (no server-side image optimization).
    unoptimized: true,
  },
  env: {
    // Empty default => same-origin API calls (frontend + backend share a host).
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL ?? "",
  },
};

export default nextConfig;
