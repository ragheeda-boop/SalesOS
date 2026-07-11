export type WidgetStatus = 'ready' | 'loading' | 'degraded' | 'error'
export type WidgetPriority = 'low' | 'medium' | 'high' | 'critical'
export type WidgetCategory = 'metrics' | 'signals' | 'decisions' | 'intelligence' | 'activity'
export type WidgetFeatureTier = 'enabled' | 'beta' | 'internal' | 'enterprise'

export interface WidgetFeatureFlag {
  enabled: boolean
  tier?: WidgetFeatureTier
  from?: string
}

export interface WidgetMetadata {
  id: string
  title: string
  description?: string
  priority?: WidgetPriority
  category?: WidgetCategory
  icon?: string
  permissions?: string[]
  refreshInterval?: number
  staleThreshold?: number
  featureFlag?: WidgetFeatureFlag
  gridColumn?: string
  minHeight?: string
}

export interface WidgetLifecycle {
  onMount?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onUnmount?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onRefresh?: (ctx: { id: string; metadata: WidgetMetadata }) => void
  onError?: (ctx: { id: string; metadata: WidgetMetadata; error: Error }) => void
  onStatusChange?: (ctx: { id: string; metadata: WidgetMetadata; status: WidgetStatus; previous: WidgetStatus }) => void
}

export interface WidgetData<T> {
  data: T | null
  status: WidgetStatus
  lastUpdated: string | null
  error: Error | null
  refetch: () => void
}

export interface WidgetRenderContext<T> {
  data: T
  status: WidgetStatus
  lastUpdated: string | null
  metadata: WidgetMetadata
  refresh: () => void
}

export interface WidgetConfig<T> {
  metadata: WidgetMetadata
  lifecycle?: WidgetLifecycle
  useData: () => WidgetData<T>
  render: (ctx: WidgetRenderContext<T>) => React.ReactNode
  fallback?: React.ReactNode
}

export interface WorkspaceWidgetEntry {
  id: string
  config: {
    gridColumn: string
    minHeight: string
    refreshIntervalMs: number
    staleThresholdMs: number
  }
}

export interface WorkspaceContextValue<W extends Record<string, unknown>> {
  widgets: W
  isLoading: boolean
  isError: boolean
  error: Error | null
  refetch: () => void
}
