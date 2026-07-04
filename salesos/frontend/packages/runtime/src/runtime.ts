import { StateRuntime } from './state-runtime'
import { SessionRuntime } from './session-runtime'
import { RealtimeRuntime } from './realtime-runtime'
import { CacheRuntime } from './cache-runtime'
import { LocalizationRuntime } from './localization-runtime'
import { AccessibilityRuntime } from './accessibility-runtime'
import { RenderingRuntime } from './rendering-runtime'
import { CollaborationRuntime } from './collaboration-runtime'
import { OfflineRuntime } from './offline-runtime'

export interface FrontendRuntime {
  state: StateRuntime
  session: SessionRuntime
  realtime: RealtimeRuntime
  cache: CacheRuntime
  localization: LocalizationRuntime
  accessibility: AccessibilityRuntime
  rendering: RenderingRuntime
  collaboration: CollaborationRuntime
  offline: OfflineRuntime

  destroy(): void
}

export interface FrontendRuntimeConfig {
  wsUrl?: string
  locale?: 'en' | 'ar' | 'fr' | 'es' | 'de' | 'tr' | 'zh' | 'ja'
  stateOptions?: ConstructorParameters<typeof StateRuntime>[0]
  cacheOptions?: ConstructorParameters<typeof CacheRuntime>[0]
  renderingOptions?: ConstructorParameters<typeof RenderingRuntime>[0]
  accessibilityOptions?: ConstructorParameters<typeof AccessibilityRuntime>[0]
  localizationOptions?: ConstructorParameters<typeof LocalizationRuntime>[0]
}

export function createFrontendRuntime(config?: FrontendRuntimeConfig): FrontendRuntime {
  const state = new StateRuntime(config?.stateOptions)
  const session = new SessionRuntime()
  const realtime = new RealtimeRuntime(config?.wsUrl || 'ws://localhost:8000/ws')
  const cache = new CacheRuntime(config?.cacheOptions)
  const localization = new LocalizationRuntime({ locale: config?.locale, ...config?.localizationOptions })
  const accessibility = new AccessibilityRuntime(config?.accessibilityOptions)
  const rendering = new RenderingRuntime(config?.renderingOptions)
  const collaboration = new CollaborationRuntime()
  const offline = new OfflineRuntime()

  return {
    state,
    session,
    realtime,
    cache,
    localization,
    accessibility,
    rendering,
    collaboration,
    offline,
    destroy() {
      realtime.disconnect()
      accessibility.destroy()
      rendering.destroy()
      collaboration.destroy()
      offline.destroy()
    },
  }
}
