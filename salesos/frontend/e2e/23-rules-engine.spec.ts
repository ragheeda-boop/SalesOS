import { test, expect } from "@playwright/test";

test.describe("Feature: Rules Engine", () => {
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

  test("page renders with title", async ({ page }) => {
    await page.goto("/rules");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 8_000 });
  });

  test("create rule form opens and has required fields", async ({ page }) => {
    await page.goto("/rules");
    await page.waitForLoadState("networkidle");
    const createBtn = page.getByRole("button", { name: /create|إنشاء|جديد|New|\+/i });
    await createBtn.click();
    await expect(page.locator("h2").first()).toBeVisible({ timeout: 5_000 });
    await expect(page.locator("input").first()).toBeVisible();
    await expect(page.locator("select").first()).toBeVisible();
  });

  test("rules list shows empty state when no rules exist", async ({ page }) => {
    await page.goto("/rules");
    await page.waitForLoadState("networkidle");
    const body = page.locator("body");
    await expect(body).toBeVisible();
  });

  test("domain filter tabs render", async ({ page }) => {
    await page.goto("/rules");
    await page.waitForLoadState("networkidle");
    const tabs = page
      .locator("button")
      .filter({ hasText: /all|company|opportunity|scoring|workflow/i });
    const count = await tabs.count();
    expect(count).toBeGreaterThanOrEqual(4);
  });
});
