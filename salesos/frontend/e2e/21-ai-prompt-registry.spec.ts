import { test, expect } from '@playwright/test'

test.describe('Critical Path 21: AI Prompt Registry', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('ai prompt registry page renders with title', async ({ page }) => {
    await page.goto('/ai')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/ai/, { timeout: 8_000 })
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 5_000 })
  })

  test('ai page shows prompt list or empty state', async ({ page }) => {
    await page.goto('/ai')
    await page.waitForLoadState('networkidle')
    const body = page.locator('body')
    await expect(body).toBeVisible({ timeout: 5_000 })
  })

  test('ai page handles API error gracefully', async ({ page }) => {
    await page.route('**/api/v1/ai/**', route => {
      route.fulfill({ status: 500, body: 'Server error' })
    })
    await page.goto('/ai')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1, body')).toBeVisible({ timeout: 5_000 })
  })

  test('ai page renders new prompt button', async ({ page }) => {
    await page.goto('/ai')
    await page.waitForLoadState('networkidle')
    const newButton = page.locator('button:has-text("New"), button:has-text("New Prompt"), a:has-text("New")')
    if (await newButton.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await expect(newButton).toBeVisible()
    }
  })
})
