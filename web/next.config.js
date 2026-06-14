// The web/Docker build is a standalone SSR server; the Capacitor app build is a
// static export (no Node runtime inside the native WebView). Gated by env so the
// default web build is unchanged — run `BUILD_TARGET=capacitor next build` for
// the static app bundle.
const isCapacitor = process.env.BUILD_TARGET === "capacitor";

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  poweredByHeader: false,
  output: isCapacitor ? "export" : "standalone",
  // `next/image` optimization needs a server; off for the static app build.
  ...(isCapacitor ? { images: { unoptimized: true } } : {}),
};

module.exports = nextConfig;
