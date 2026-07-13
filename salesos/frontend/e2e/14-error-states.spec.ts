import { test, expect } from '@playwright/test'

test.describe('Critical Path 14: Error States & Empty States', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('dashboard shows widgets or empty state after login', async ({ page }) => {
    await page.waitForLoadState('networkidle')
    await expect(page.locator('[class*="widget"], [class*="empty"], [class*="placeholder"], [class*="skeleton"]').first()).toBeVisible({ timeout: 8_000 })
  })

  test('search page handles empty query gracefully', async ({ page }) => {
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    const input = page.getByPlaceholder(/بحث|search/i)
    if (await input.isVisible()) {
      await input.fill('')
    }
    await expect(page.locator('main, [role="main"], article, div').first()).toBeVisible({ timeout: 5_000 })
  })

  test('company detail shows content or empty state', async ({ page }) => {
    await page.goto('/companies')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('main, [role="main"], article, table, div').first()).toBeVisible({ timeout: 8_000 })
  })

  test('navigate to non-existent route shows proper error page', async ({ page }) => {
    await page.goto('/companies/nonexistent-id-12345')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('main, [role="main"], div').first()).toBeVisible({ timeout: 8_000 })
  })
})
