export type WidgetStatus = 'ready' | 'loading' | 'degraded' | 'error'

export type WidgetPriority = 'low' | 'medium' | 'high' | 'critical'
export type WidgetCategory = 'metrics' | 'signals' | 'decisions' | 'intelligence' | 'activity' | 'enterprise'
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

// ── Decision Provider Types ────────────────────────────────────

export type DecisionContextType = 'company' | 'revenue' | 'pipeline' | 'dashboard'

export interface DecisionFactor {
  name: string
  value: number
  weight: number
  description: string
}

export interface DecisionContextData {
  context_type: DecisionContextType
  factors: DecisionFactor[]
  confidence: number
  summary: string
  generated_at: string
}

export interface NBAFeedItem {
  id: string
  decision_id?: string
  company_id: string
  company_name: string
  action: string
  reason: string
  confidence: number
  confidence_label: 'high' | 'medium' | 'low'
  priority: number
  source: string
  status: string
  created_at: string
}

export interface NBAFeedResponse {
  items: NBAFeedItem[]
  total: number
  page: number
  page_size: number
  has_more: boolean
  generated_at: string
  cached: boolean
}

export interface DecisionWidgetRenderContext<T> extends WidgetRenderContext<T> {
  decision: DecisionContextData | null
  nbaItems: NBAFeedItem[]
  isDecisionLoading: boolean
}

export interface DecisionWidgetConfig<T> {
  metadata: WidgetMetadata
  lifecycle?: WidgetLifecycle
  useData: () => WidgetData<T>
  useDecision: (tenantId: string, context?: Record<string, string>) => DecisionContextData | null
  useNBA?: () => NBAFeedItem[]
  render: (ctx: DecisionWidgetRenderContext<T>) => React.ReactNode
  fallback?: React.ReactNode
}
