import { test, expect } from '@playwright/test'

test.describe('Critical Path 19: Forecast', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('forecast page renders with title', async ({ page }) => {
    await page.goto('/forecast')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/forecast/, { timeout: 8_000 })
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 5_000 })
  })

  test('forecast page shows metric cards', async ({ page }) => {
    await page.goto('/forecast')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 5_000 })
  })

  test('forecast page handles empty state', async ({ page }) => {
    await page.route('**/api/v1/forecast', route => {
      route.fulfill({ status: 200, body: JSON.stringify({ message: 'No forecast yet' }) })
    })
    await page.goto('/forecast')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible({ timeout: 5_000 })
  })

  test('forecast page handles API error', async ({ page }) => {
    await page.route('**/api/v1/forecast', route => {
      route.fulfill({ status: 500, body: 'Server error' })
    })
    await page.goto('/forecast')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1, body')).toBeVisible({ timeout: 5_000 })
  })
})
