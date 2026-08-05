import { test, expect } from "@playwright/test";

test.describe("Feature: Analytics Data Verification", () => {
  test.skip(
    !process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL,
    "Credentials env vars not set"
  );

  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!);
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!);
    await page.getByRole("button", { name: /دخول|Sign in/i }).click();
    await page.waitForURL(/dashboard/, { timeout: 10_000 });
  });

  test("KPI values display correct formatted values", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    await expect(page.getByText("$12.5M").or(page.getByText("$42.0M"))).toBeVisible({
      timeout: 5_000,
    });
  });

  test("chart SVG elements render in chart containers", async ({ page }) => {
    await page.goto("/analytics");
    await page.waitForLoadState("networkidle");
    const chartCards = page.locator("svg");
    const svgCount = await chartCards.count();
    expect(svgCount).toBeGreaterThanOrEqual(1);
    for (const svg of await chartCards.all()) {
      await expect(svg).toBeVisible();
    }
  });
});
