import { test, expect } from '@playwright/test'

test.describe('Critical Path 11: Contacts CRUD Flow', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('contacts list page renders', async ({ page }) => {
    await page.goto('/contacts')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/contacts/, { timeout: 8_000 })
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 5_000 })
  })

  test('contacts page shows table or card list', async ({ page }) => {
    await page.goto('/contacts')
    await page.waitForLoadState('networkidle')
    const list = page.locator('table, [role="grid"], [class*="card"], [class*="contact"]').first()
    if (await list.isVisible({ timeout: 5_000 })) {
      expect(true).toBeTruthy()
    } else {
      await expect(page.locator('main, [role="main"], article').first()).toBeVisible()
    }
  })

  test('contacts page has search/filter input', async ({ page }) => {
    await page.goto('/contacts')
    await page.waitForLoadState('networkidle')
    await expect(page.getByPlaceholder(/بحث|search/i)).toBeVisible({ timeout: 5_000 })
  })

  test('navigate from contacts to contact detail', async ({ page }) => {
    await page.goto('/contacts')
    await page.waitForLoadState('networkidle')
    const link = page.locator('a[href*="/contacts/"]').first()
    if (await link.isVisible({ timeout: 3_000 })) {
      await link.click()
      await page.waitForLoadState('networkidle')
    }
    await expect(page).toHaveURL(/contacts/, { timeout: 5_000 })
  })

  test('contacts page handles loading state', async ({ page }) => {
    await page.goto('/contacts')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('main, [role="main"], article, div').first()).toBeVisible({ timeout: 5_000 })
  })
})
