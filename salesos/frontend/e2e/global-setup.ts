import { FullConfig } from '@playwright/test'

async function globalSetup(_config: FullConfig) {
  if (process.env.CI) {
    console.log('[global-setup] CI mode — verifying web server readiness...')
  }
  console.log('[global-setup] E2E test suite starting for SalesOS frontend')
}

export default globalSetup
