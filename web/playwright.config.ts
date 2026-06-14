import { defineConfig, devices } from "@playwright/test";

// Runs against an already-running stack (the docker-compose deploy). Override
// the target with PLAYWRIGHT_BASE_URL; defaults to the deploy's web port (3002).
const baseURL = process.env.PLAYWRIGHT_BASE_URL ?? "http://localhost:3002";

export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  retries: 0,
  reporter: "list",
  use: {
    baseURL,
    trace: "on-first-retry",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
