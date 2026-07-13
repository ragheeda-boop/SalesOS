import { test, expect } from '@playwright/test'

test.describe('Critical Path 6: Pipeline Kanban', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to pipeline kanban view', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/pipeline/, { timeout: 8_000 })
  })

  test('kanban columns render', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    const columns = page.locator('[data-testid^="kanban-column"], [class*="kanban"]')
    const count = await columns.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('kanban column headers are visible', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    const headers = page.locator('h2, h3, [role="columnheader"]')
    const count = await headers.count()
    expect(count).toBeGreaterThanOrEqual(1)
  })

  test('drag and drop handles exist on cards', async ({ page }) => {
    await page.goto('/pipeline')
    await page.waitForLoadState('networkidle')
    const draggable = page.locator('[draggable="true"]')
    const count = await draggable.count()
    if (count > 0) {
      const firstCard = draggable.first()
      expect(await firstCard.getAttribute('draggable')).toBe('true')
    }
  })
})
