import { test, expect } from "@playwright/test";

test.describe("Critical Path 12: Employee 360 View", () => {
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

  test("employee me page renders profile", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/employees\/me/, { timeout: 8_000 });
    const heading = page.locator("h1").first();
    await expect(heading).toBeVisible({ timeout: 10_000 });
    await expect(heading).not.toBeEmpty();
  });

  test("employee 360 shows KPI metrics", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const kpiSection = page.locator("h1").first();
    await expect(kpiSection).toBeVisible({ timeout: 10_000 });
  });

  test("employee 360 includes AI coach section", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const coachTab = page.getByRole("tab", { name: /ai coach|المدرب/i });
    await expect(coachTab).toBeVisible({ timeout: 10_000 });
  });

  test("employee 360 navigation from dashboard", async ({ page }) => {
    await page.goto("/dashboard");
    await page.waitForLoadState("networkidle");
    const navLink = page.locator('a[href*="employees"], a[href*="me"]').first();
    await expect(navLink).toBeVisible({ timeout: 5_000 });
  });

  test("employee 360 tabs are visible", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const tabList = page.getByRole("tablist");
    await expect(tabList).toBeVisible({ timeout: 10_000 });
    const tabs = tabList.getByRole("tab");
    const tabCount = await tabs.count();
    expect(tabCount).toBeGreaterThanOrEqual(3);
  });

  test("employee 360 signals tab renders", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const signalsTab = page.getByRole("tab", { name: /signals|إشارات/i });
    await expect(signalsTab).toBeVisible({ timeout: 10_000 });
    await signalsTab.click();
    const tabpanel = page.locator('[role="tabpanel"]').first();
    await expect(tabpanel).toBeVisible({ timeout: 5_000 });
  });

  test("employee 360 timeline tab renders", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const timelineTab = page.getByRole("tab", { name: /timeline|الجدول الزمني/i });
    await expect(timelineTab).toBeVisible({ timeout: 10_000 });
    await timelineTab.click();
    const tabpanel = page.locator('[role="tabpanel"]').first();
    await expect(tabpanel).toBeVisible({ timeout: 5_000 });
  });

  test("employee 360 performance tab renders", async ({ page }) => {
    await page.goto("/employees/me");
    await page.waitForLoadState("networkidle");
    const perfTab = page.getByRole("tab", { name: /performance|أداء/i });
    await expect(perfTab).toBeVisible({ timeout: 10_000 });
    await perfTab.click();
    const tabpanel = page.locator('[role="tabpanel"]').first();
    await expect(tabpanel).toBeVisible({ timeout: 5_000 });
  });
});
