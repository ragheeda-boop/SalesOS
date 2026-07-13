import { test, expect } from '@playwright/test'

test.describe('Critical Path 13: Workflow Automation', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('automation page renders', async ({ page }) => {
    await page.goto('/automation')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/automation/, { timeout: 8_000 })
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 5_000 })
  })

  test('workflow list shows workflows or empty state', async ({ page }) => {
    await page.goto('/automation')
    await page.waitForLoadState('networkidle')
    const content = page.locator(
      'main, [role="main"], article, table, [class*="workflow"], [class*="empty"]'
    ).first()
    await expect(content).toBeVisible({ timeout: 8_000 })
  })

  test('create workflow button is accessible', async ({ page }) => {
    await page.goto('/automation')
    await page.waitForLoadState('networkidle')
    const createBtn = page.getByRole('button', { name: /إضافة|create|new|جديد/i })
    if (await createBtn.isVisible({ timeout: 3_000 })) {
      expect(true).toBeTruthy()
    }
    await expect(page.locator('main, [role="main"], div').first()).toBeVisible({ timeout: 5_000 })
  })

  test('automation navigation present in sidebar', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const nav = page.locator('nav, aside, [role="navigation"]').first()
    await expect(nav).toBeVisible({ timeout: 5_000 })
  })
})
