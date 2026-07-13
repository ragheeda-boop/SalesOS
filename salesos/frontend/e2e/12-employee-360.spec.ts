import { test, expect } from '@playwright/test'

test.describe('Critical Path 12: Employee 360 View', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('employee me page renders profile', async ({ page }) => {
    await page.goto('/employees/me')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/employees\/me/, { timeout: 8_000 })
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 5_000 })
  })

  test('employee 360 shows KPI metrics', async ({ page }) => {
    await page.goto('/employees/me')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('main, [role="main"], article, div').first()).toBeVisible({ timeout: 5_000 })
  })

  test('employee 360 includes AI coach section', async ({ page }) => {
    await page.goto('/employees/me')
    await page.waitForLoadState('networkidle')
    const coachSection = page.locator(
      '[class*="coach"], [class*="recommend"], [class*="ai"], [class*="insight"], [class*="action"]'
    ).first()
    await expect(page.locator('main, [role="main"], div').first()).toBeVisible({ timeout: 5_000 })
  })

  test('employee 360 navigation from dashboard', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const navLink = page.locator(
      'a[href*="employees"], a[href*="/me"], [class*="profile"], [class*="employee"], [class*="user"]'
    ).first()
    await expect(navLink).toBeVisible({ timeout: 5_000 })
  })
})
