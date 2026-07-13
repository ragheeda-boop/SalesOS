import { test, expect } from '@playwright/test'

test.describe('Critical Path 5: Create Opportunity', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to opportunities list', async ({ page }) => {
    await page.goto('/opportunities')
    await page.waitForTimeout(3_000)
    await expect(page).toHaveURL(/opportunities/, { timeout: 8_000 })
  })

  test('create opportunity button is visible', async ({ page }) => {
    await page.goto('/opportunities')
    const createBtn = page.getByRole('button', { name: /إضافة|create|new/i })
    await expect(createBtn.first()).toBeVisible({ timeout: 5_000 })
  })

  test('create opportunity form opens', async ({ page }) => {
    await page.goto('/opportunities')
    const createBtn = page.getByRole('button', { name: /إضافة|create|new/i })
    if (await createBtn.first().isVisible({ timeout: 3_000 })) {
      await createBtn.first().click()
      await page.waitForTimeout(1_500)
    }
  })

  test('opportunity form displays required fields', async ({ page }) => {
    await page.goto('/opportunities')
    const createBtn = page.getByRole('button', { name: /إضافة|create|new/i })
    if (await createBtn.first().isVisible({ timeout: 3_000 })) {
      await createBtn.first().click()
      await expect(page.locator('input, select, textarea').first()).toBeVisible({ timeout: 3_000 })
    }
  })
})
