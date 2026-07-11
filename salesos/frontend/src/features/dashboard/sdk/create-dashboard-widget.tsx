import { createWidget } from './create-widget'
import { useDashboardContext } from '../_providers/dashboard-provider'
import { getWidgetConfig, type WidgetId } from '../_registry/widget-config'
import type { WidgetConfig, WidgetMetadata, WidgetLifecycle } from './types'

type DashboardWidgetMeta = Omit<Partial<WidgetMetadata>, 'id'>
interface DashboardWidgetOverrides<T> {
  metadata?: DashboardWidgetMeta
  lifecycle?: WidgetLifecycle
  fallback?: React.ReactNode
  render: WidgetConfig<T>['render']
}

export function createDashboardWidget<T>(
  id: WidgetId,
  overrides: DashboardWidgetOverrides<T>,
) {
  const config = getWidgetConfig(id)

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
      const ctx = useDashboardContext()
      const widget = ctx.widgets[id]
      return {
        data: widget.data as T,
        status: widget.status,
        lastUpdated: widget.lastUpdated,
        error: ctx.error,
        refetch: ctx.refetch,
      }
    },
    render: overrides.render,
  })
}
