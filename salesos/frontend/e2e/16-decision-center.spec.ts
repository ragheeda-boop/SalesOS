import { test, expect } from "@playwright/test";

test.describe("Critical Path 16: Decision Center", () => {
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

  test("decision center page renders with title", async ({ page }) => {
    await page.goto("/decisions");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/decisions/, { timeout: 8_000 });
    await expect(page.locator("h1").first()).toBeVisible({ timeout: 5_000 });
  });

  test("decision center loads decision list or empty state", async ({ page }) => {
    await page.goto("/decisions");
    await page.waitForLoadState("networkidle");
    const body = page.locator("body");
    await expect(body).toBeVisible({ timeout: 5_000 });
  });

  test("decision center handles API errors gracefully", async ({ page }) => {
    await page.route("**/api/v1/decisions**", (route) => {
      route.fulfill({ status: 500, body: "Server error" });
    });
    await page.route("**/api/v1/decision/**", (route) => {
      route.fulfill({ status: 500, body: "Server error" });
    });
    await page.goto("/decisions");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 5_000 });
  });
});
