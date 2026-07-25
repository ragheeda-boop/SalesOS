import { setFeatureFlagResolver } from '../widget-feature-flags'
import type { WidgetFeatureFlag } from '../types'

export function mockFeatureFlagsAll() {
  setFeatureFlagResolver({
    isEnabled: () => true,
  })
}

export function mockFeatureFlagsNone() {
  setFeatureFlagResolver({
    isEnabled: () => false,
  })
}

export function mockFeatureFlagsCustom(resolver: (flag: WidgetFeatureFlag) => boolean) {
  setFeatureFlagResolver({
    isEnabled: resolver,
  })
}
