import { FullConfig } from '@playwright/test'

async function globalTeardown(_config: FullConfig) {
  console.log('[global-teardown] E2E test suite complete')
}

export default globalTeardown
