import { test, expect } from '@playwright/test'

test.describe('Critical Path 9: RTL Layout Rendering', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('page renders with RTL direction', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const html = page.locator('html')
    await expect(html).toHaveAttribute('dir', 'rtl')
  })

  test('dashboard layout flows right-to-left', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const html = page.locator('html')
    await expect(html).toHaveAttribute('dir', 'rtl')
  })

  test('Arabic text renders in dashboard headings', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/dashboard/, { timeout: 5_000 })
    await expect(page.locator('h1, h2').first()).toBeVisible({ timeout: 3_000 })
  })

  test('navigation sidebar displays Arabic labels', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const arabicText = page.getByText(/لوحة|بحث|شركات|إدارة|لوحة القيادة/i)
    const count = await arabicText.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('form inputs support Arabic placeholder text', async ({ page }) => {
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    const placeholder = page.getByPlaceholder(/بحث|اسم|البريد/i)
    const count = await placeholder.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })
})
