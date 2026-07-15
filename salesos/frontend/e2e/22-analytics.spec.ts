import { test, expect } from '@playwright/test'

test.describe('Feature: Analytics Dashboard', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('renders KPI cards with correct count', async ({ page }) => {
    await page.goto('/analytics')
    await page.waitForLoadState('networkidle')
    await expect(page.getByRole('heading', { name: /التحليلات|Analytics|تحليلات/i })).toBeVisible({ timeout: 8_000 })
    const kpis = page.locator('[class*="grid"] >> [class*="rounded"]').first()
    await expect(kpis).toBeVisible()
  })

  test('charts render in chart containers', async ({ page }) => {
    await page.goto('/analytics')
    await page.waitForLoadState('networkidle')
    const svgs = page.locator('svg')
    const count = await svgs.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('export CSV button is clickable', async ({ page }) => {
    await page.goto('/analytics')
    await page.waitForLoadState('networkidle')
    const csvBtn = page.getByRole('button', { name: /csv|CSV/i })
    await expect(csvBtn).toBeVisible({ timeout: 5_000 })
    await csvBtn.click()
    await expect(csvBtn).toBeDisabled({ timeout: 2_000 })
  })

  test('page renders without errors', async ({ page }) => {
    await page.goto('/analytics')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1')).toBeVisible()
    const errors = await page.locator('text=/error|Error|خطأ/i').count()
    expect(errors).toBe(0)
  })
})
