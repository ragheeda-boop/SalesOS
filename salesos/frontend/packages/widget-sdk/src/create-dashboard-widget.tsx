import { createWidget } from './create-widget'
import type { WidgetConfig, WidgetMetadata, WidgetLifecycle, WidgetStatus } from './types'

export interface DashboardContextValue {
  widgets: Record<string, { data: unknown; status: WidgetStatus; lastUpdated: string | null }>
  error: Error | null
  refetch: () => void
}

export interface WidgetConfigEntry {
  refreshIntervalMs?: number
  staleThresholdMs?: number
  gridColumn?: string
  minHeight?: string
}

type DashboardContextHook = () => DashboardContextValue
type WidgetConfigGetter = (id: string) => WidgetConfigEntry

let _useDashboardContext: DashboardContextHook = () => ({
  widgets: {},
  error: null,
  refetch: () => {},
})
let _getWidgetConfig: WidgetConfigGetter = () => ({})

export function setDashboardDependencies(
  useDashboardContext: DashboardContextHook,
  getWidgetConfig: WidgetConfigGetter,
) {
  _useDashboardContext = useDashboardContext
  _getWidgetConfig = getWidgetConfig
}

type DashboardWidgetMeta = Omit<Partial<WidgetMetadata>, 'id'>
interface DashboardWidgetOverrides<T> {
  metadata?: DashboardWidgetMeta
  lifecycle?: WidgetLifecycle
  fallback?: React.ReactNode
  render: WidgetConfig<T>['render']
}

export function createDashboardWidget<T>(
  id: string,
  overrides: DashboardWidgetOverrides<T>,
) {
  const config = _getWidgetConfig(id)

  return createWidget<T>({
    metadata: {
      id,
      title: overrides.metadata?.title ?? '',
      refreshInterval: config.refreshIntervalMs,
      staleThreshold: config.staleThresholdMs,
      gridColumn: config.gridColumn,
      minHeight: config.minHeight,
      ...overrides.metadata,
    } as WidgetMetadata,
    lifecycle: overrides.lifecycle,
    fallback: overrides.fallback,
    useData: () => {
      const ctx = _useDashboardContext()
      const widget = ctx.widgets[id]
      return {
        data: widget?.data as T,
        status: widget?.status ?? 'loading',
        lastUpdated: widget?.lastUpdated ?? null,
        error: ctx.error,
        refetch: ctx.refetch,
      }
    },
    render: overrides.render,
  })
}
