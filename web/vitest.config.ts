import { fileURLToPath } from "node:url";

import { defineConfig } from "vitest/config";

// Resolve the "@/..." path alias (matches tsconfig paths) so unit tests can
// import modules that use it. Pure-logic tests run in the node environment.
export default defineConfig({
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./", import.meta.url)),
    },
  },
  test: {
    environment: "node",
    include: ["lib/**/*.test.ts"],
  },
});
