import { createDashboardWidget } from './create-dashboard-widget'
import { useDashboardContext } from '../_providers/dashboard-provider'
import { getWidgetConfig, type WidgetId } from '../_registry/widget-config'
import type {
  WidgetMetadata,
  WidgetLifecycle,
  DecisionContextData,
  DecisionWidgetRenderContext,
  NBAFeedItem,
} from './types'

type DashboardWidgetMeta = Omit<Partial<WidgetMetadata>, 'id'>

interface DecisionWidgetOverrides<T> {
  metadata?: DashboardWidgetMeta
  lifecycle?: WidgetLifecycle
  fallback?: React.ReactNode
  useDecision: (tenantId: string, context?: Record<string, string>) => DecisionContextData | null
  useNBA?: () => NBAFeedItem[]
  render: (ctx: DecisionWidgetRenderContext<T>) => React.ReactNode
}

/**
 * Creates a decision-enabled dashboard widget that extends `createDashboardWidget`
 * with DecisionProvider context and optional NBA feed data.
 *
 * Follows the Container/View pattern: this factory is the Container,
 * the `render` prop is the View.
 *
 * @example
 * ```tsx
 * const MissionCenterDecision = createDecisionEnabledWidget<MissionData>(
 *   'missionCenter',
 *   {
 *     metadata: { title: 'Mission Center' },
 *     useDecision: (tenantId) => useCompanyDecision(tenantId),
 *     useNBA: () => useNBAFeed(),
 *     render: (ctx) => <MissionCenterView {...ctx} />,
 *   },
 * )
 * ```
 */
export function createDecisionEnabledWidget<T>(
  id: WidgetId,
  overrides: DecisionWidgetOverrides<T>,
) {
  const config = getWidgetConfig(id)

  return createDashboardWidget<T>(id, {
    metadata: {
      title: overrides.metadata?.title ?? '',
      refreshInterval: config.refreshIntervalMs,
      staleThreshold: config.staleThresholdMs,
      gridColumn: config.gridColumn,
      minHeight: config.minHeight,
      ...overrides.metadata,
    } as WidgetMetadata,
    lifecycle: overrides.lifecycle,
    fallback: overrides.fallback,
    render: (ctx) => {
      const { widgets, isLoading, isError, error, refetch } = useDashboardContext()
      const widget = widgets[id]

      // Call the decision hook with available context
      const tenantId = (widget.data as unknown as Record<string, string>)?.tenant_id ?? ''
      const companyId = (widget.data as unknown as Record<string, string>)?.company_id ?? ''
      const decision = overrides.useDecision(tenantId, { company_id: companyId })

      // Call the NBA hook if provided
      const nbaItems = overrides.useNBA?.() ?? []

      const decisionCtx: DecisionWidgetRenderContext<T> = {
        data: ctx.data,
        status: ctx.status,
        lastUpdated: ctx.lastUpdated,
        metadata: ctx.metadata,
        refresh: ctx.refresh,
        decision,
        nbaItems,
        isDecisionLoading: isLoading,
      }

      return overrides.render(decisionCtx)
    },
  })
}
