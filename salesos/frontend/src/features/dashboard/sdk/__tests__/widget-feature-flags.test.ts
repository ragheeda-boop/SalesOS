import { WidgetFeatureFlags } from '../widget-feature-flags'

describe('WidgetFeatureFlags', () => {
  it('returns false for unknown flags', () => {
    const flags = new WidgetFeatureFlags({})
    expect(flags.isEnabled('new-ui')).toBe(false)
  })

  it('returns true for enabled flags', () => {
    const flags = new WidgetFeatureFlags({ 'new-ui': true, 'beta': false })
    expect(flags.isEnabled('new-ui')).toBe(true)
    expect(flags.isEnabled('beta')).toBe(false)
  })

  it('accepts widget-specific overrides', () => {
    const flags = new WidgetFeatureFlags({ 'new-ui': false })
    expect(flags.isEnabled('new-ui', 'widget-1')).toBe(false)
  })
})
