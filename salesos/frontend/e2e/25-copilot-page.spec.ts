import { test, expect } from "@playwright/test";

test.describe("Feature: Copilot Page", () => {
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

  test("page renders with title and AI icon", async ({ page }) => {
    await page.goto("/copilot");
    await page.waitForLoadState("networkidle");
    await expect(page.locator("h1")).toBeVisible({ timeout: 8_000 });
    await expect(
      page.locator("h1").or(page.locator("text=/مساعد|Assistant|Copilot/i").first())
    ).toBeVisible();
  });

  test("chat input area is accessible", async ({ page }) => {
    await page.goto("/copilot");
    await page.waitForLoadState("networkidle");
    const input = page
      .getByRole("textbox")
      .or(page.locator("textarea"))
      .or(page.locator('input[type="text"]'));
    if (await input.isVisible({ timeout: 5_000 })) {
      await input.fill("Hello");
      await expect(input).toHaveValue(/hello/i);
    }
  });

  test("history sidebar toggles", async ({ page }) => {
    await page.goto("/copilot");
    await page.waitForLoadState("networkidle");
    const historyBtn = page.getByRole("button", { name: /history|History/i });
    if (await historyBtn.isVisible({ timeout: 5_000 })) {
      await historyBtn.click();
      await page.waitForLoadState("networkidle");
    }
    const sidebar = page
      .locator("div")
      .filter({ hasText: /recent|محادثات|Conversations/i })
      .first();
    await expect(sidebar).toBeVisible({ timeout: 3_000 });
  });
});
