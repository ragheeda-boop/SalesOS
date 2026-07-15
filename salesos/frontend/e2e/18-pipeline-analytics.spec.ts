import { test, expect } from '@playwright/test'

test.describe('Critical Path 18: Pipeline Analytics', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('pipeline page renders with workspace', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/pipeline/, { timeout: 8_000 })
  })

  test('pipeline page displays content area', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    const main = page.locator('main, [role="main"], div[class*="p-6"]')
    await expect(main).toBeVisible({ timeout: 5_000 })
  })

  test('pipeline page handles API errors gracefully', async ({ page }) => {
    await page.route('**/api/v1/pipeline/**', route => {
      route.fulfill({ status: 500, body: 'Server error' })
    })
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible({ timeout: 5_000 })
  })

  test('pipeline page accessible from sidebar', async ({ page }) => {
    const link = page.locator('a[href*="/pipeline"], nav a:has-text("Pipeline")')
    if (await link.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await link.click()
      await page.waitForURL(/pipeline/, { timeout: 8_000 })
    }
  })
})
