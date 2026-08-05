import { test, expect } from "@playwright/test";

test.describe("Critical Path 27: V3 Company 360 Intelligence Tab", () => {
  test.skip(
    !process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL,
    "E2E_USER_EMAIL/E2E_USER_PASSWORD env vars not set"
  );

  test.beforeEach(async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!);
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!);
    await page.getByRole("button", { name: /دخول|Sign in/i }).click();
    await page.waitForURL(/dashboard/, { timeout: 10_000 });
  });

  test("navigate to V3 companies list and open a company", async ({ page }) => {
    await page.goto("/v3/companies");
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveURL(/\/v3\/companies/, { timeout: 8_000 });

    const firstCompany = page.locator('a[href*="/v3/companies/"]').first();
    await expect(firstCompany).toBeVisible({ timeout: 5_000 });
    await firstCompany.click();
    await page.waitForURL(/\/v3\/companies\/[^/]+$/, { timeout: 5_000 });
  });

  test("Intelligence tab renders all widgets without console errors", async ({ page }) => {
    const consoleErrors: string[] = [];
    page.on("console", (msg) => {
      if (msg.type() === "error") consoleErrors.push(msg.text());
    });

    await page.goto("/v3/companies");
    await page.waitForLoadState("networkidle");

    const firstCompany = page.locator('a[href*="/v3/companies/"]').first();
    if (!(await firstCompany.isVisible({ timeout: 3_000 }))) {
      test.skip(true, "No companies in list — cannot test Intelligence tab");
      return;
    }
    await firstCompany.click();
    await page.waitForURL(/\/v3\/companies\/[^/]+$/, { timeout: 5_000 });

    const intelligenceTab = page.getByRole("tab", { name: /intelligence|intelligent/i });
    await expect(intelligenceTab).toBeVisible({ timeout: 5_000 });
    await intelligenceTab.click();

    await page.waitForLoadState("networkidle");

    const widgetTitles = [
      "Company DNA",
      "AI Recommendation",
      "Decision Makers",
      "Relationship Graph",
      "Buying Journey",
      "Golden Record",
      "Signals",
      "Smart Timeline",
      "Government Intelligence",
      "Document Intelligence",
    ];

    for (const title of widgetTitles) {
      const heading = page.getByRole("heading", { name: title });
      await expect(heading).toBeVisible({ timeout: 10_000 });
    }

    const criticalErrors = consoleErrors.filter(
      (e) => !e.includes("favicon") && !e.includes("otlp") && !e.includes("404")
    );
    expect(criticalErrors).toEqual([]);
  });

  test("Intelligence tab issues only one API call on initial load", async ({ page }) => {
    const intelligenceRequests: string[] = [];
    page.on("request", (req) => {
      if (req.url().includes("/intelligence")) {
        intelligenceRequests.push(req.url());
      }
    });

    await page.goto("/v3/companies");
    await page.waitForLoadState("networkidle");

    const firstCompany = page.locator('a[href*="/v3/companies/"]').first();
    if (!(await firstCompany.isVisible({ timeout: 3_000 }))) {
      test.skip(true, "No companies in list — cannot test Intelligence tab");
      return;
    }
    await firstCompany.click();
    await page.waitForURL(/\/v3\/companies\/[^/]+$/, { timeout: 5_000 });

    const intelligenceTab = page.getByRole("tab", { name: /intelligence|intelligent/i });
    await intelligenceTab.click();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(2_000);

    expect(intelligenceRequests.length).toBeLessThanOrEqual(1);
  });

  test("Intelligence tab uses cache on tab switch", async ({ page }) => {
    const intelligenceRequests: string[] = [];
    page.on("request", (req) => {
      if (req.url().includes("/intelligence")) {
        intelligenceRequests.push(req.url());
      }
    });

    await page.goto("/v3/companies");
    await page.waitForLoadState("networkidle");

    const firstCompany = page.locator('a[href*="/v3/companies/"]').first();
    if (!(await firstCompany.isVisible({ timeout: 3_000 }))) {
      test.skip(true, "No companies in list — cannot test Intelligence tab");
      return;
    }
    await firstCompany.click();
    await page.waitForURL(/\/v3\/companies\/[^/]+$/, { timeout: 5_000 });

    const intelligenceTab = page.getByRole("tab", { name: /intelligence|intelligent/i });
    await intelligenceTab.click();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1_000);

    const callsAfterFirstLoad = intelligenceRequests.length;

    const contactsTab = page.getByRole("tab", { name: /contacts|جهات/i });
    await contactsTab.click();
    await page.waitForTimeout(500);

    await intelligenceTab.click();
    await page.waitForLoadState("networkidle");
    await page.waitForTimeout(1_000);

    expect(intelligenceRequests.length).toBe(callsAfterFirstLoad);
  });

  test("page refresh does not break Intelligence tab", async ({ page }) => {
    await page.goto("/v3/companies");
    await page.waitForLoadState("networkidle");

    const firstCompany = page.locator('a[href*="/v3/companies/"]').first();
    if (!(await firstCompany.isVisible({ timeout: 3_000 }))) {
      test.skip(true, "No companies in list — cannot test Intelligence tab");
      return;
    }
    await firstCompany.click();
    await page.waitForURL(/\/v3\/companies\/[^/]+$/, { timeout: 5_000 });

    const intelligenceTab = page.getByRole("tab", { name: /intelligence|intelligent/i });
    await intelligenceTab.click();
    await page.waitForLoadState("networkidle");

    await page.reload();
    await page.waitForLoadState("networkidle");

    const intelligenceTabAfterReload = page.getByRole("tab", { name: /intelligence|intelligent/i });
    await expect(intelligenceTabAfterReload).toBeVisible({ timeout: 5_000 });
    await intelligenceTabAfterReload.click();
    await page.waitForLoadState("networkidle");

    const signalsHeading = page.getByRole("heading", { name: "Signals" });
    await expect(signalsHeading).toBeVisible({ timeout: 10_000 });
  });
});
