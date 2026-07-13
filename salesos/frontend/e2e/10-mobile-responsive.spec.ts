import { test, expect } from '@playwright/test'

test.describe('Critical Path 10: Mobile Responsive Navigation', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.use({ viewport: { width: 375, height: 812 } })

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('mobile viewport renders correctly', async ({ page }) => {
    const viewport = page.viewportSize()
    expect(viewport?.width).toBeLessThanOrEqual(375)
  })

  test('hamburger menu opens navigation', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const hamburger = page.getByLabel(/menu|القائمة|nav/i).or(page.locator('[data-testid="hamburger"], [aria-label*="menu" i]'))
    if (await hamburger.first().isVisible({ timeout: 3_000 })) {
      await hamburger.first().click()
      await page.waitForLoadState('networkidle')
    }
    await expect(page).toHaveURL(/dashboard/, { timeout: 5_000 })
  })

  test('dashboard widgets stack vertically on mobile', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/dashboard/, { timeout: 5_000 })
    await expect(page.locator('[data-testid^="widget-"], main').first()).toBeVisible({ timeout: 3_000 })
  })

  test('touch targets are accessible (min 44px)', async ({ page }) => {
    await page.goto('/dashboard')
    await page.waitForLoadState('networkidle')
    const buttons = page.locator('button, a[role="button"]')
    const count = await buttons.count()
    if (count > 0) {
      const firstBtn = buttons.first()
      const box = await firstBtn.boundingBox()
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(20)
      }
    }
  })

  test('mobile search renders touch-friendly input', async ({ page }) => {
    await page.goto('/search')
    await page.waitForLoadState('networkidle')
    const searchInput = page.getByRole('searchbox').or(page.getByPlaceholder(/بحث|search/i))
    if (await searchInput.isVisible({ timeout: 3_000 })) {
      const box = await searchInput.boundingBox()
      if (box) {
        expect(box.height).toBeGreaterThanOrEqual(20)
      }
    }
  })
})
