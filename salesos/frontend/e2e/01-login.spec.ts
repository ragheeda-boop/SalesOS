import { test, expect } from '@playwright/test'

const VALID_EMAIL = process.env.E2E_USER_EMAIL!
const VALID_PASSWORD = process.env.E2E_USER_PASSWORD!

test.describe('Critical Path 1: Login Flow', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'E2E_USER_EMAIL/E2E_USER_PASSWORD env vars not set')
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
  })

  test('login page renders login form', async ({ page }) => {
    await expect(page.getByRole('heading', { name: /تسجيل الدخول|Login/i })).toBeVisible()
    await expect(page.getByLabel(/البريد|email/i)).toBeVisible()
    await expect(page.getByLabel(/كلمة المرور|password/i)).toBeVisible()
    await expect(page.getByRole('button', { name: /دخول|Sign in/i })).toBeVisible()
  })

  test('login succeeds with valid credentials', async ({ page }) => {
    await page.getByLabel(/البريد|email/i).fill(VALID_EMAIL)
    await page.getByLabel(/كلمة المرور|password/i).fill(VALID_PASSWORD)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()

    await expect(page).toHaveURL(/dashboard/, { timeout: 10_000 })
  })

  test('login fails with invalid password', async ({ page }) => {
    await page.getByLabel(/البريد|email/i).fill(VALID_EMAIL)
    await page.getByLabel(/كلمة المرور|password/i).fill('WrongPassword999!')
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()

    await expect(page.getByText(/خطأ|invalid|incorrect|غير صحيح/i)).toBeVisible({ timeout: 5_000 })
  })

  test('login fails with empty email', async ({ page }) => {
    await page.getByLabel(/كلمة المرور|password/i).fill(VALID_PASSWORD)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()

    await expect(page.getByText(/مطلوب|required/i)).toBeVisible({ timeout: 5_000 })
  })

  test('password field masks input', async ({ page }) => {
    const passwordField = page.getByLabel(/كلمة المرور|password/i)
    await passwordField.fill('TestPassword123!')
    const type = await passwordField.getAttribute('type')
    expect(type).toBe('password')
  })
})
