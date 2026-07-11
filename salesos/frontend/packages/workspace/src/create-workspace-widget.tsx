import { createWidget } from './create-widget'
import type { WidgetConfig, WidgetMetadata, WidgetLifecycle, WidgetData, WorkspaceContextValue } from './types'

export interface WorkspaceWidgetConfig {
  id: string
  gridColumn?: string
  minHeight?: string
  refreshIntervalMs?: number
  staleThresholdMs?: number
}

interface CreateWorkspaceWidgetOverrides<T> {
  metadata?: Omit<Partial<WidgetMetadata>, 'id'>
  lifecycle?: WidgetLifecycle
  fallback?: React.ReactNode
  render: WidgetConfig<T>['render']
}

export function createWorkspaceWidget<T, W extends Record<string, unknown>>(
  config: WorkspaceWidgetConfig,
  useWorkspaceContext: () => WorkspaceContextValue<W>,
  widgetSelector: (widgets: W) => WidgetData<T>,
  overrides: CreateWorkspaceWidgetOverrides<T>,
) {
  return createWidget<T>({
    metadata: {
      id: config.id,
      title: overrides.metadata?.title ?? '',
      refreshInterval: config.refreshIntervalMs,
      staleThreshold: config.staleThresholdMs,
      gridColumn: config.gridColumn,
      minHeight: config.minHeight,
      ...overrides.metadata,
    },
    lifecycle: overrides.lifecycle,
    fallback: overrides.fallback,
    useData: () => {
      const ctx = useWorkspaceContext()
      return widgetSelector(ctx.widgets)
    },
    render: overrides.render,
  })
}
