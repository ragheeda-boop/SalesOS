import { test, expect } from '@playwright/test'

/**
 * FE-S04-08 — E2E hooks for Owner Platform tenant admin UI.
 * Smoke only: navigate + open create modal (no mutating create/suspend).
 * Skips without credentials (same pattern as 08-admin-panel).
 * Full Stage 7 provision mutate remains approval-gated.
 */
test.describe('FE-S04-08 Admin tenants Owner Platform hooks', () => {
  test.skip(
    !process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL,
    'Credentials env vars not set',
  )

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('admin tenants page exposes Owner Platform hooks', async ({ page }) => {
    await page.goto('/admin/tenants')
    await page.waitForLoadState('networkidle')
    await expect(page).toHaveURL(/admin\/tenants/, { timeout: 8_000 })
    await expect(page.getByTestId('admin-tenants-page')).toBeVisible({
      timeout: 8_000,
    })
    await expect(page.getByTestId('admin-tenants-new')).toBeVisible()

    await page.getByTestId('admin-tenants-new').click()
    await expect(page.getByTestId('admin-tenants-create-modal')).toBeVisible({
      timeout: 5_000,
    })
    await expect(page.getByTestId('admin-tenants-create-name')).toBeVisible()
    await expect(page.getByTestId('admin-tenants-create-slug')).toBeVisible()
    await expect(page.getByTestId('admin-tenants-create-submit')).toBeVisible()
  })
})
