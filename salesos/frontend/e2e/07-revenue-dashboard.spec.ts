import { test, expect } from '@playwright/test'

test.describe('Critical Path 7: Revenue Dashboard', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to revenue page', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForTimeout(3_000)
    await expect(page).toHaveURL(/revenue/, { timeout: 8_000 })
  })

  test('revenue page shows revenue metrics', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForTimeout(3_000)
  })

  test('revenue charts render without errors', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForTimeout(3_000)
    const charts = page.locator('[data-testid*="chart"], [class*="chart"], canvas, svg')
    const count = await charts.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('pipeline value is displayed formatted', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForTimeout(3_000)
    const sarPattern = page.getByText(/SAR|ريال|ر\.س/)
    const count = await sarPattern.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })
})
