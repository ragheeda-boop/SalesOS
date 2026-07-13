import { test, expect } from '@playwright/test'

test.describe('Critical Path 8: Admin Panel Navigation', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to admin panel', async ({ page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3_000)
    await expect(page).toHaveURL(/admin/, { timeout: 8_000 })
  })

  test('admin panel renders sections', async ({ page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3_000)
    const sections = page.locator('h2, h3, [role="tab"], nav a')
    const count = await sections.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('admin settings page loads', async ({ page }) => {
    await page.goto('/admin/settings')
    await page.waitForTimeout(3_000)
    await expect(page).toHaveURL(/admin/, { timeout: 8_000 })
  })

  test('admin user management page loads', async ({ page }) => {
    await page.goto('/admin/users')
    await page.waitForTimeout(3_000)
  })
})
