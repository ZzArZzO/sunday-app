import type { CapacitorConfig } from "@capacitor/cli";

// Capacitor wraps the static export (`out/`, produced by
// `BUILD_TARGET=capacitor next build`) into native iOS + Android apps.
// `appId` is a placeholder bundle id — set it to the real reverse-DNS id before
// store submission.
const config: CapacitorConfig = {
  appId: "com.sunday.app",
  appName: "Sunday",
  webDir: "out",
  server: {
    androidScheme: "https",
  },
};

export default config;
