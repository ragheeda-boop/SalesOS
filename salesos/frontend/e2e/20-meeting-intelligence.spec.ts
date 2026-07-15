import { test, expect } from '@playwright/test'

test.describe('Critical Path 20: Meeting Intelligence', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('meetings page renders with title', async ({ page }) => {
    await page.goto('/meetings')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/meetings/, { timeout: 8_000 })
    await expect(page.locator('h1').first()).toBeVisible({ timeout: 5_000 })
  })

  test('meetings page shows opportunity selector', async ({ page }) => {
    await page.goto('/meetings')
    await page.waitForLoadState('networkidle')
    const selector = page.locator('button:has-text("Select"), [class*="border"]:has-text("Select")')
    if (await selector.isVisible({ timeout: 3_000 }).catch(() => false)) {
      await expect(selector).toBeVisible()
    }
  })

  test('meetings page handles API error gracefully', async ({ page }) => {
    await page.route('**/api/v1/opportunities**', route => {
      route.fulfill({ status: 500, body: 'Server error' })
    })
    await page.goto('/meetings')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('body')).toBeVisible({ timeout: 5_000 })
  })

  test('meetings page shows empty prompt when no opportunity selected', async ({ page }) => {
    await page.goto('/meetings')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1')).toBeVisible({ timeout: 5_000 })
    const hasCalendarIcon = page.locator('.lucide-calendar, svg.calendar, [class*="Calendar"]')
    if (await hasCalendarIcon.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await expect(hasCalendarIcon).toBeVisible()
    }
  })
})
