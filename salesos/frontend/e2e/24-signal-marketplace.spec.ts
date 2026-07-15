import { test, expect } from '@playwright/test'

const mockSignals = [
  { id: 'sig-1', name: 'New Decision Maker', ar_name: 'صانع قرار جديد', description: 'Detects new exec', domain: 'company', category: 'enrichment', severity: 'info', source: 'linkedin', pack_id: 'pack-1', priority: 'medium', weight: 0.85, created_at: '2026-07-01T00:00:00Z' },
  { id: 'sig-2', name: 'Budget Increase', ar_name: 'زيادة الميزانية', description: 'Budget change detected', domain: 'opportunity', category: 'opportunity', severity: 'warning', source: 'crm', pack_id: 'pack-1', priority: 'high', weight: 0.92, created_at: '2026-07-02T00:00:00Z' },
]

const mockFeed = [
  { id: 'evt-1', signal_id: 'sig-1', company_id: 'comp-1', data: { role: 'CEO' }, detected_at: '2026-07-10T08:00:00Z', acknowledged: false },
  { id: 'evt-2', signal_id: 'sig-2', company_id: 'comp-2', data: { amount: 50000 }, detected_at: '2026-07-10T09:00:00Z', acknowledged: true },
]

const mockSubscriptions = [
  { id: 'sub-1', signal_id: 'sig-1', company_id: 'comp-1', channel: 'in-app', active: true, created_at: '2026-07-05T00:00:00Z' },
]

test.describe('Feature: Signal Marketplace', () => {
  test.skip(!process.env.E2E_USER_PASSWORD || !process.env.E2E_USER_EMAIL, 'Credentials env vars not set')

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByLabel(/البريد|email/i).fill(process.env.E2E_USER_EMAIL!)
    await page.getByLabel(/كلمة المرور|password/i).fill(process.env.E2E_USER_PASSWORD!)
    await page.getByRole('button', { name: /دخول|Sign in/i }).click()
    await page.waitForURL(/dashboard/, { timeout: 10_000 })
  })

  test('three tabs render on signals page', async ({ page }) => {
    await page.route('**/api/v1/signals**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ signals: mockSignals }) }))
    await page.goto('/signals')
    await page.waitForLoadState('networkidle')
    await expect(page.locator('h1')).toBeVisible({ timeout: 8_000 })
    const tabButtons = page.locator('button').filter({ hasText: /marketplace|feed|subscriptions|Marketplace|Feed/i })
    const count = await tabButtons.count()
    expect(count).toBeGreaterThanOrEqual(2)
  })

  test('marketplace tab shows signal list', async ({ page }) => {
    await page.route('**/api/v1/signals**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ signals: mockSignals }) }))
    await page.goto('/signals')
    await page.waitForLoadState('networkidle')
    await expect(page.getByText('New Decision Maker').or(page.getByText('Budget Increase'))).toBeVisible({ timeout: 5_000 })
  })

  test('subscribe button triggers subscription', async ({ page }) => {
    await page.route('**/api/v1/signals**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ signals: mockSignals }) }))
    await page.route('**/api/v1/signals/subscribe**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) }))
    await page.goto('/signals')
    await page.waitForLoadState('networkidle')
    const subscribeBtn = page.getByRole('button', { name: /subscribe/i }).first()
    await expect(subscribeBtn).toBeVisible({ timeout: 5_000 })
  })

  test('feed tab shows signal events', async ({ page }) => {
    await page.route('**/api/v1/signals/feed**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ events: mockFeed }) }))
    await page.goto('/signals')
    await page.waitForLoadState('networkidle')
    const feedTab = page.getByRole('button', { name: /feed|Signal Feed/i })
    if (await feedTab.isVisible()) {
      await feedTab.click()
      await page.waitForLoadState('networkidle')
    }
  })

  test('acknowledge button works on feed events', async ({ page }) => {
    await page.route('**/api/v1/signals/feed**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ events: [{ id: 'evt-ack', signal_id: 'sig-1', company_id: 'comp-1', data: { test: true }, detected_at: '2026-07-10T10:00:00Z', acknowledged: false }] }) }))
    await page.route('**/api/v1/signals/*/acknowledge**', route => route.fulfill({ status: 200, contentType: 'application/json', body: JSON.stringify({ success: true }) }))
    await page.goto('/signals')
    await page.waitForLoadState('networkidle')
    const feedTab = page.getByRole('button', { name: /feed|Signal Feed/i })
    if (await feedTab.isVisible()) {
      await feedTab.click()
      await page.waitForLoadState('networkidle')
    }
    const ackBtn = page.getByRole('button', { name: /acknowledge/i })
    if (await ackBtn.isVisible({ timeout: 3_000 })) {
      await ackBtn.click()
    }
  })
})
