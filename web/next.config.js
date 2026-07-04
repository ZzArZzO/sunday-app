// Three build targets, three output modes:
// - Capacitor app: static export (no Node runtime inside the native WebView)
// - Vercel: no override — Vercel's own build wires up serverless functions
//   itself and doesn't run a bundled server.js, so "standalone" output there
//   silently breaks routing (builds fine, 404s at runtime) instead of erroring.
// - Self-hosted (Docker on Hetzner, via web/Dockerfile): standalone SSR server.
const isCapacitor = process.env.BUILD_TARGET === "capacitor";
const isVercel = process.env.VERCEL === "1";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  ...(isCapacitor ? { output: "export" } : isVercel ? {} : { output: "standalone" }),
  // `next/image` optimization needs a server; off for the static app build.
  ...(isCapacitor ? { images: { unoptimized: true } } : {}),
};

module.exports = nextConfig;
