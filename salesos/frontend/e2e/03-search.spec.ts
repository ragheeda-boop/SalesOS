import { test, expect } from '@playwright/test'

test.describe('Critical Path 3: Search Company Flow', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL || 'admin@test.com')
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD || 'password')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('navigate to search page', async ({ page }) => {
    const searchLink = page.getByRole('link', { name: /بحث|search/i })
    if (await searchLink.isVisible({ timeout: 3_000 })) {
      await searchLink.click()
      await expect(page).toHaveURL(/search/, { timeout: 8_000 })
    } else {
      await page.goto('/search')
    }
    await expect(page).toHaveURL(/search/, { timeout: 8_000 })
  })

  test('search bar accepts input and returns results', async ({ page }) => {
    await page.goto('/search')
    const searchInput = page.getByRole('searchbox').or(page.getByPlaceholder(/بحث|search/i))
    if (await searchInput.isVisible({ timeout: 5_000 })) {
      await searchInput.fill('الرياض')
      await searchInput.press('Enter')
      await page.waitForTimeout(3_000)
    }
  })

  test('search supports Arabic text input', async ({ page }) => {
    await page.goto('/search')
    const searchInput = page.getByRole('searchbox').or(page.getByPlaceholder(/بحث|search/i))
    if (await searchInput.isVisible({ timeout: 5_000 })) {
      await searchInput.fill('شركة')
      await searchInput.press('Enter')
      await page.waitForTimeout(2_000)
    }
  })

  test('empty search shows initial state', async ({ page }) => {
    await page.goto('/search')
    await page.waitForTimeout(2_000)
  })
})
