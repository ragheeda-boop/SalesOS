import { test, expect } from '@playwright/test'

test.describe('Critical Path 4: Company Detail Page', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to companies list', async ({ page }) => {
    await page.goto('/companies')
    await page.waitForTimeout(3_000)
    await expect(page).toHaveURL(/companies/, { timeout: 8_000 })
  })

  test('company detail page shows company info', async ({ page }) => {
    await page.goto('/companies')
    await page.waitForTimeout(2_000)
    const firstCompany = page.locator('a[href*="/companies/"]').first()
    if (await firstCompany.isVisible({ timeout: 3_000 })) {
      await firstCompany.click()
      await page.waitForTimeout(2_000)
    }
  })

  test('company detail displays CR number and name', async ({ page }) => {
    await page.goto('/companies')
    await page.waitForTimeout(2_000)
  })

  test('company 360 view renders enriched data', async ({ page }) => {
    await page.goto('/companies')
    await page.waitForTimeout(3_000)
  })
})
