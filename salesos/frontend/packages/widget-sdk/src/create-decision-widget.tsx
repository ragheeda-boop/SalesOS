import { createDashboardWidget, setDashboardDependencies } from "./create-dashboard-widget";
import type {
  WidgetMetadata,
  WidgetLifecycle,
  DecisionContextData,
  DecisionWidgetRenderContext,
  NBAFeedItem,
} from "./types";
type DashboardWidgetMeta = Omit<Partial<WidgetMetadata>, "id">;

interface DecisionWidgetOverrides<T> {
  metadata?: DashboardWidgetMeta;
  lifecycle?: WidgetLifecycle;
  fallback?: React.ReactNode;
  useDecision: (tenantId: string, context?: Record<string, string>) => DecisionContextData | null;
  useNBA?: () => NBAFeedItem[];
  render: (ctx: DecisionWidgetRenderContext<T>) => React.ReactNode;
}

export function createDecisionEnabledWidget<T>(id: string, overrides: DecisionWidgetOverrides<T>) {
  return createDashboardWidget<T>(id, {
    metadata: {
      title: overrides.metadata?.title ?? "",
      ...overrides.metadata,
    } as WidgetMetadata,
    lifecycle: overrides.lifecycle,
    fallback: overrides.fallback,
    render: (ctx) => {
      const tenantId = (ctx.data as unknown as Record<string, string>)?.tenant_id ?? "";
      const companyId = (ctx.data as unknown as Record<string, string>)?.company_id ?? "";
      const decision = overrides.useDecision(tenantId, { company_id: companyId });
      const nbaItems = overrides.useNBA?.() ?? [];

      const decisionCtx: DecisionWidgetRenderContext<T> = {
        data: ctx.data,
        status: ctx.status,
        lastUpdated: ctx.lastUpdated,
        metadata: ctx.metadata,
        refresh: ctx.refresh,
        decision,
        nbaItems,
        isDecisionLoading: false,
      };

      return overrides.render(decisionCtx);
    },
  });
}

export { setDashboardDependencies };
export type { DashboardContextValue } from "./create-dashboard-widget";
