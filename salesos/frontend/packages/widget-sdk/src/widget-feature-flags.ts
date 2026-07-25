import type { WidgetFeatureFlag } from './types'

export interface FeatureFlagResolver {
  isEnabled(flag: WidgetFeatureFlag): boolean
}

let resolver: FeatureFlagResolver = { isEnabled: () => true }

export function setFeatureFlagResolver(r: FeatureFlagResolver) {
  resolver = r
}

export function isFeatureEnabled(flag?: WidgetFeatureFlag): boolean {
  if (!flag) return true
  if (!flag.enabled) return false
  return resolver.isEnabled(flag)
}
