import { expect, test } from "@playwright/test";

// Smoke coverage of the critical surfaces. Assumes a running stack (the
// docker-compose deploy) — see playwright.config.ts for the base URL.
// Run: `npx playwright install chromium && npm run test:e2e`.

test.describe("critical surfaces render", () => {
  test("dashboard shows holdings, allocation, benchmark and tax", async ({ page }) => {
    await page.goto("/dashboard");
    await expect(page.getByText("By asset class")).toBeVisible();
    await expect(page.getByText("Holdings map")).toBeVisible();
    await expect(page.getByText("Performance vs benchmark")).toBeVisible();
    await expect(page.getByText("Positions")).toBeVisible();
    // a11y: allocation visuals expose accessible names, not colour alone.
    await expect(
      page.getByRole("img", { name: /Allocation by asset class/i }),
    ).toBeVisible();
    await expect(page.getByRole("img", { name: /Holdings by market value/i })).toBeVisible();
  });

  test("briefing shows the hero and what-changed section", async ({ page }) => {
    await page.goto("/briefing");
    await expect(page.getByText("The one number that matters")).toBeVisible();
    await expect(page.getByText("What changed this week")).toBeVisible();
  });

  test("upload shows the import dropzone and the sample link", async ({ page }) => {
    await page.goto("/upload");
    await expect(page.getByText("Drop a CSV, or browse")).toBeVisible();
    await expect(page.getByRole("link", { name: /sample portfolio/i })).toBeVisible();
  });

  test("assistant shows the AI label, grouped prompts and input", async ({ page }) => {
    await page.goto("/assistant");
    await expect(page.getByText(/AI assistant/i).first()).toBeVisible();
    await expect(page.getByText("Understand my portfolio")).toBeVisible();
    await expect(page.getByPlaceholder(/Ask about your portfolio/i)).toBeVisible();
  });
});
