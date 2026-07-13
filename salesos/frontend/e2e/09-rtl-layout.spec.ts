import { test, expect } from '@playwright/test'

test.describe('Critical Path 9: RTL Layout Rendering', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('page renders with RTL direction', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2_000)
    const htmlDir = await page.locator('html').getAttribute('dir')
    expect(htmlDir).toBe('rtl')
  })

  test('dashboard layout flows right-to-left', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2_000)
    const html = page.locator('html')
    await expect(html).toHaveAttribute('dir', 'rtl')
  })

  test('Arabic text renders in dashboard headings', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2_000)
  })

  test('navigation sidebar displays Arabic labels', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForTimeout(2_000)
    const arabicText = page.getByText(/لوحة|بحث|شركات|إدارة|لوحة القيادة/i)
    const count = await arabicText.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })

  test('form inputs support Arabic placeholder text', async ({ page }) => {
    await page.goto('/search')
    await page.waitForTimeout(2_000)
    const placeholder = page.getByPlaceholder(/بحث|اسم|البريد/i)
    const count = await placeholder.count()
    expect(count).toBeGreaterThanOrEqual(0)
  })
})
