import { isFeatureEnabled, setFeatureFlagResolver } from '../widget-feature-flags'
import type { WidgetFeatureFlag } from '../types'

describe('widget-feature-flags', () => {
  beforeEach(() => {
    setFeatureFlagResolver({ isEnabled: () => true })
  })

  it('returns true when no flag provided', () => {
    expect(isFeatureEnabled()).toBe(true)
  })

  it('returns false when flag is not enabled', () => {
    expect(isFeatureEnabled({ enabled: false, name: 'new-ui' } as WidgetFeatureFlag)).toBe(false)
  })

  it('delegates to resolver when flag is enabled', () => {
    const resolver = jest.fn().mockReturnValue(true)
    setFeatureFlagResolver({ isEnabled: resolver })
    const flag = { enabled: true, name: 'new-ui' } as WidgetFeatureFlag
    expect(isFeatureEnabled(flag)).toBe(true)
    expect(resolver).toHaveBeenCalledWith(flag)
  })
})
