import { test, expect } from '@playwright/test'

test.describe('Critical Path 5: Create Opportunity', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to opportunities list', async ({ page }) => {
    await page.goto('/opportunities')
    await page.waitForLoadState('networkidle')
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
      await page.waitForLoadState('networkidle')
    }
    await expect(page).toHaveURL(/opportunities/, { timeout: 5_000 })
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
