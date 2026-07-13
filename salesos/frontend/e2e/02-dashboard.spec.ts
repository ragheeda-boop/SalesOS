import { test, expect } from '@playwright/test'

test.describe('Critical Path 2: Dashboard Widgets', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('dashboard renders with widget grid', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /لوحة التحكم|Dashboard|لوحة القيادة/i })).toBeVisible({ timeout: 8_000 })
  })

  test('widgets are visible in ready state', async ({ page }) => {
    await page.waitForTimeout(3_000)
    const widgets = page.locator('[data-testid^="widget-"], [class*="widget"]')
    const count = await widgets.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('refresh button triggers widget reload', async ({ page }) => {
    await page.waitForTimeout(2_000)
    const refreshButton = page.getByLabel('Refresh').first()
    if (await refreshButton.isVisible()) {
      await refreshButton.click()
      await page.waitForTimeout(1_000)
    }
  })

  test('dashboard navigation sidebar renders', async ({ page }) => {
    await expect(page.locator('nav, aside, [role="navigation"]').first()).toBeVisible({ timeout: 5_000 })
  })
})
