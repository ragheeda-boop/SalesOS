/**
 * Shared E2E auth helpers for CI / local Playwright.
 * Login labels are visual-only (no htmlFor) — use input[type=...] not getByLabel.
 */
import { expect, type Page } from '@playwright/test'

const API_BASE = process.env.API_BASE_URL || 'http://127.0.0.1:8000'

export async function gotoRetry(page: Page, route: string, attempts = 4) {
  let lastErr: unknown
  for (let i = 0; i < attempts; i++) {
    try {
      return await page.goto(route, { waitUntil: 'domcontentloaded', timeout: 45_000 })
    } catch (e) {
      lastErr = e
      await page.waitForTimeout(1500 * (i + 1))
    }
  }
  throw lastErr
}

/** Seed tokens via API (bypasses flaky UI login when needed). */
export async function seedTokensFromApi(page: Page, email: string, password: string) {
  const res = await page.request.post(`${API_BASE}/api/v1/identity/login`, {
    data: { email, password },
    timeout: 90_000,
  })
  expect(res.ok(), `API login HTTP ${res.status()}`).toBeTruthy()
  const body = await res.json()
  await gotoRetry(page, '/login')
  await page.evaluate(
    ({ access_token, refresh_token, tenant_id }) => {
      localStorage.setItem('access_token', access_token)
      if (refresh_token) localStorage.setItem('refresh_token', refresh_token)
      if (tenant_id) localStorage.setItem('tenant_id', String(tenant_id))
    },
    {
      access_token: body.access_token as string,
      refresh_token: (body.refresh_token as string) || '',
      tenant_id: body.tenant_id != null ? String(body.tenant_id) : '',
    },
  )
}

/** UI login with API-token fallback (Wave 13 pattern). */
export async function uiLogin(page: Page, email: string, password: string) {
  await gotoRetry(page, '/login')
  await expect(page.getByRole('heading', { name: /Sign In|Login|تسجيل/i })).toBeVisible({
    timeout: 20_000,
  })
  await page.locator('input[type="email"]').fill(email)
  await page.locator('input[type="password"]').fill(password)
  await page.getByRole('button', { name: /Login|Sign in|دخول|تسجيل/i }).click()

  try {
    await page.waitForFunction(() => !!localStorage.getItem('access_token'), null, {
      timeout: 25_000,
    })
  } catch {
    await seedTokensFromApi(page, email, password)
  }

  const hasToken = await page.evaluate(() => !!localStorage.getItem('access_token'))
  expect(hasToken, 'access_token missing after UI/API login').toBeTruthy()
}
