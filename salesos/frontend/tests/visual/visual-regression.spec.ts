import { test, expect } from "@playwright/test";
import path from "path";

const BASE_URL = process.env.BASE_URL || "http://localhost:3000";
const SCREENSHOT_DIR = path.resolve(__dirname, "../../e2e/screenshots");

test.describe("Visual Regression Tests", () => {
  test.beforeEach(async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 800 });
  });

  test("login page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("login-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("dashboard page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("dashboard-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("companies list page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/companies`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("companies-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("form page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/companies/new`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("form-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("search page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/search`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("search-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("404 page visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/nonexistent-page`);
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("404-page.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });
});

test.describe("Visual Regression — Dark Mode", () => {
  test("dashboard dark mode visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/dashboard`);
    await page.evaluate(() => document.documentElement.classList.add("dark"));
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("dashboard-dark.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });

  test("login page dark mode visual comparison", async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);
    await page.evaluate(() => document.documentElement.classList.add("dark"));
    await page.waitForLoadState("networkidle");
    await expect(page).toHaveScreenshot("login-dark.png", {
      maxDiffPixels: 100,
      fullPage: true,
    });
  });
});
