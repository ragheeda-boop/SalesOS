import { defineConfig, devices } from '@playwright/test'

/**
 * Wave 13 UI smoke — uses already-running FE (Docker :3000).
 * Does not start npm run dev (avoids port 3002 collision).
 */
export default defineConfig({
  testDir: '.',
  testMatch: ['e2e/smoke-auth-ui.spec.ts'],
  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: [['list']],

  use: {
    baseURL: process.env.BASE_URL || 'http://127.0.0.1:3000',
    trace: 'off',
    screenshot: 'only-on-failure',
    video: 'off',
    locale: 'en-GB',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  timeout: 120_000,
  expect: { timeout: 15_000 },

  globalSetup: require.resolve('./e2e/global-setup'),
  globalTeardown: require.resolve('./e2e/global-teardown'),
})
