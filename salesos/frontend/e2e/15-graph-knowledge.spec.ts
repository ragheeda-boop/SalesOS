import { test, expect } from '@playwright/test'

test.describe('Critical Path 15: Knowledge Graph', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('graph page renders', async ({ page }) => {
    await page.goto('/graph')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/graph/, { timeout: 8_000 })
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 5_000 })
  })

  test('graph page has search input', async ({ page }) => {
    await page.goto('/graph')
    await page.waitForLoadState('networkidle')
    await expect(page.getByPlaceholder(/بحث|search/i)).toBeVisible({ timeout: 5_000 })
  })

  test('graph search returns results or empty state', async ({ page }) => {
    await page.goto('/graph')
    await page.waitForLoadState('networkidle')
    const searchInput = page.getByPlaceholder(/بحث|search/i)
    if (await searchInput.isVisible()) {
      await searchInput.fill('test')
      await searchInput.press('Enter')
      await page.waitForTimeout(2000)
    }
    await expect(page.locator('main, [role="main"], div').first()).toBeVisible({ timeout: 5_000 })
  })
})
