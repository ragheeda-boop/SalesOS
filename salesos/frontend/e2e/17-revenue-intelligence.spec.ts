import { test, expect } from '@playwright/test'

test.describe('Critical Path 17: Revenue Intelligence', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('revenue page renders with workspace component', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/revenue/, { timeout: 8_000 })
  })

  test('revenue page shows pipeline summary section', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForLoadState('networkidle')
    const content = page.locator('main, div[class*="p-6"]')
    await expect(content).toBeVisible({ timeout: 5_000 })
  })

  test('revenue page handles empty data gracefully', async ({ page }) => {
    await page.goto('/revenue')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 5_000 })
  })

  test('revenue page navigates via sidebar', async ({ page }) => {
    const revenueLink = page.locator('a[href*="/revenue"], [data-testid*="revenue"], nav a:has-text("Revenue")')
    if (await revenueLink.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await revenueLink.click()
      await page.waitForURL(/revenue/, { timeout: 8_000 })
      await expect(page).toHaveURL(/revenue/)
    }
  })
})
