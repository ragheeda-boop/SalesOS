"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { RefreshCw, ArrowRight, Phone, Mail, MessageSquare, Calendar, FileText, Clock, CheckCircle2, AlertTriangle, TrendingUp, Zap, Target, Brain } from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import { getTenantId } from "@/lib/hooks/useTenant";
import { signalActionKeys, hitlKeys } from "@/lib/queryKeys";
import apiClient from "@/lib/api/client";
import { getFeedbackAnalytics } from "@/lib/api/hitl";
import { track } from "@/lib/analytics";

interface Action {
  id: string;
  nba_id: string;
  company_name: string;
  action_type: string;
  status: string;
  outcome: string;
  notes: string;
  created_at: string;
  completed_at: string | null;
}

interface DashboardMetrics {
  total_signals: number;
  qualified_signals: number;
  total_accounts: number;
  active_actions: number;
  completed_actions: number;
  by_priority: Record<string, number>;
  by_urgency: Record<string, number>;
  by_action_type: Record<string, number>;
}

interface SignalActionListResponse {
  count: number;
  actions: Action[];
}

interface SignalActionDashboardResponse {
  accounts_with_signals: number;
  critical_accounts: number;
  pending_actions: number;
  completed_actions: number;
  priority_breakdown: Record<string, number>;
  signal_breakdown: unknown[];
}

const ACTION_ICONS: Record<string, typeof Phone> = {
  call: Phone,
  email: Mail,
  whatsapp: MessageSquare,
  meeting: Calendar,
  create_opportunity: Target,
  proposal: FileText,
  follow_up: Clock,
  research: Brain,
  no_action: Clock,
};

const ACTION_COLORS: Record<string, string> = {
  call: "text-orange-600",
  email: "text-blue-600",
  whatsapp: "text-emerald-600",
  meeting: "text-purple-600",
  create_opportunity: "text-amber-600",
  proposal: "text-indigo-600",
  follow_up: "text-gray-600",
  research: "text-teal-600",
  no_action: "text-gray-400",
};

const STATUS_COLORS: Record<string, string> = {
  pending: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  skipped: "bg-gray-100 text-gray-600",
};

function formatActionType(type: string): string {
  return type.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function ActionCard({ action, onComplete }: { action: Action; onComplete: (id: string) => void }) {
  const Icon = ACTION_ICONS[action.action_type] || Clock;
  const iconColor = ACTION_COLORS[action.action_type] || "text-gray-600";
  const isPending = action.status === "pending";

  return (
    <div className="flex items-start gap-3 p-4 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] hover:border-[var(--border-secondary)] transition-colors">
      <div className={`mt-0.5 ${iconColor}`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <h4 className="text-sm font-medium text-[var(--text-primary)] truncate">
            {action.company_name}
          </h4>
          <span className={`text-[10px] px-1.5 py-0.5 rounded font-medium ${STATUS_COLORS[action.status]}`}>
            {action.status}
          </span>
        </div>
        <p className="text-xs text-[var(--text-muted)] mt-0.5">
          {formatActionType(action.action_type)}
        </p>
        <p className="text-xs text-[var(--text-secondary)] mt-1 line-clamp-2">
          {action.notes}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[10px] text-[var(--text-muted)] whitespace-nowrap">
          {formatTimeAgo(action.created_at)}
        </span>
        {isPending && (
          <button
            onClick={() => onComplete(action.id)}
            className="text-[var(--text-muted)] hover:text-[var(--color-success)] transition-colors"
            title="Mark completed"
          >
            <CheckCircle2 className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

function MetricCard({ label, value, icon: Icon, color }: { label: string; value: number; icon: typeof TrendingUp; color: string }) {
  return (
    <div className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)]">
      <Icon className={`w-5 h-5 ${color}`} />
      <div>
        <div className="text-lg font-semibold text-[var(--text-primary)]">{value}</div>
        <div className="text-[11px] text-[var(--text-muted)] uppercase tracking-wide">{label}</div>
      </div>
    </div>
  );
}

function ActionBreakdown({ actions }: { actions: Action[] }) {
  const counts: Record<string, number> = {};
  for (const a of actions) {
    if (a.status === "pending") {
      counts[a.action_type] = (counts[a.action_type] || 0) + 1;
    }
  }
  const sorted = Object.entries(counts).sort((a, b) => b[1] - a[1]);
  if (sorted.length === 0) return null;

  return (
    <div className="space-y-2">
      {sorted.map(([type, count]) => {
        const Icon = ACTION_ICONS[type] || Clock;
        const color = ACTION_COLORS[type] || "text-gray-600";
        return (
          <div key={type} className="flex items-center gap-2">
            <Icon className={`w-4 h-4 ${color}`} />
            <span className="text-sm text-[var(--text-primary)] flex-1">{formatActionType(type)}</span>
            <span className="text-sm font-medium text-[var(--text-secondary)]">{count}</span>
          </div>
        );
      })}
    </div>
  );
}

export default function SalesDashboardPage() {
  const { ready, hasToken } = useAccessToken();
  const queryClient = useQueryClient();

  const { data: actions, isLoading, isError: actionsError, refetch } = useQuery({
    queryKey: signalActionKeys.actions(),
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/signal-actions/actions", {
        params: { status: "pending" },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      const payload = res.data as SignalActionListResponse | Action[];
      return Array.isArray(payload) ? payload : payload.actions;
    },
    enabled: ready && hasToken,
    refetchInterval: 30000,
  });

  const { data: metrics } = useQuery({
    queryKey: signalActionKeys.dashboard(),
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/signal-actions/dashboard", {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      const payload = res.data as SignalActionDashboardResponse;
      return {
        total_signals: payload.accounts_with_signals,
        qualified_signals: payload.accounts_with_signals,
        total_accounts: payload.accounts_with_signals,
        active_actions: payload.pending_actions,
        completed_actions: payload.completed_actions,
        by_priority: payload.priority_breakdown,
        by_urgency: {},
        by_action_type: {},
      } satisfies DashboardMetrics;
    },
    enabled: ready && hasToken,
  });

  const completeMutation = useMutation({
    mutationFn: async (actionId: string) => {
      await apiClient.post("/api/v1/signal-actions/complete", {
        action_id: actionId,
        outcome: "positive",
        notes: "Marked complete from Sales Dashboard",
      }, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
    },
    onSuccess: (_result, actionId) => {
      const action = actions?.find((candidate) => candidate.id === actionId);
      track({
        type: "nba.executed",
        metadata: {
          actionId,
          recommendationId: action?.nba_id,
          actionType: action?.action_type,
          surface: "sales_dashboard",
        },
      });
      queryClient.invalidateQueries({ queryKey: signalActionKeys.actions() });
      queryClient.invalidateQueries({ queryKey: signalActionKeys.dashboard() });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
    },
  });

  const { data: analytics } = useQuery({
    queryKey: hitlKeys.analytics(),
    queryFn: () => getFeedbackAnalytics(undefined, getTenantId()),
    enabled: ready && hasToken,
  });

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/sales-dashboard" />;
  if (isLoading) return <LoadingState label="Loading dashboard…" />;
  if (actionsError)
    return (
      <div className="min-h-screen">
        <PageHeader
          title="Sales Dashboard"
          description="Your daily sales execution view — priority accounts, next actions, evidence"
        />
        <div className="px-6">
          <ErrorState
            title="Could not load dashboard"
            description="Signal actions failed to load. Check your connection and try again."
            onRetry={() => void refetch()}
          />
        </div>
      </div>
    );

  const pendingActions = actions ?? [];
  const immediateCount = pendingActions.filter((a) => {
    const notes = a.notes.toLowerCase();
    return notes.includes("urgent") || notes.includes("immediate") || notes.includes("critical");
  }).length;

  return (
    <div className="min-h-screen">
      <PageHeader
        title="Sales Dashboard"
        description="Your daily sales execution view — priority accounts, next actions, evidence"
        actions={
          <button
            onClick={() => refetch()}
            className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            Refresh
          </button>
        }
      />

      <div className="px-6 pb-8">
        {/* Metrics Row */}
        <div className="grid grid-cols-5 gap-4 mb-6">
          <MetricCard label="Pending Actions" value={metrics?.active_actions ?? pendingActions.length} icon={Zap} color="text-orange-600" />
          <MetricCard label="Completed" value={metrics?.completed_actions ?? 0} icon={CheckCircle2} color="text-green-600" />
          <MetricCard label="Accounts" value={metrics?.total_accounts ?? 0} icon={TrendingUp} color="text-blue-600" />
          <MetricCard label="Signals" value={metrics?.total_signals ?? 0} icon={Brain} color="text-purple-600" />
          <MetricCard label="Immediate" value={immediateCount} icon={AlertTriangle} color="text-red-600" />
        </div>

        <div className="grid grid-cols-3 gap-6">
          {/* Main: Action List */}
          <div className="col-span-2 space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide">
                Today&apos;s Actions ({pendingActions.length})
              </h2>
            </div>
            {pendingActions.length === 0 ? (
              <EmptyState
                title="No pending actions"
                description="All caught up! Run a research scan on a company to generate new signal-driven actions."
              />
            ) : (
              <div className="space-y-2">
                {pendingActions.map((action) => (
                  <ActionCard
                    key={action.id}
                    action={action}
                    onComplete={(id) => completeMutation.mutate(id)}
                  />
                ))}
              </div>
            )}
          </div>

          {/* Sidebar: Breakdown */}
          <div className="space-y-6">
            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                Action Breakdown
              </h3>
              <ActionBreakdown actions={pendingActions} />
            </div>

            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                By Priority
              </h3>
              <div className="space-y-2">
                {["CRITICAL", "HIGH", "MEDIUM", "LOW", "NOISE"].map((level) => {
                  const count = metrics?.by_priority?.[level] ?? 0;
                  if (count === 0) return null;
                  return (
                    <div key={level} className="flex items-center gap-2">
                      <span className={`w-2 h-2 rounded-full ${level === "CRITICAL" ? "bg-red-500" : level === "HIGH" ? "bg-orange-500" : level === "MEDIUM" ? "bg-yellow-500" : level === "LOW" ? "bg-blue-500" : "bg-gray-300"}`} />
                      <span className="text-sm text-[var(--text-primary)] flex-1">{level}</span>
                      <span className="text-sm font-medium text-[var(--text-secondary)]">{count}</span>
                    </div>
                  );
                })}
              </div>
            </div>

            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                How It Works
              </h3>
              <div className="space-y-2 text-xs text-[var(--text-muted)]">
                <p className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
                  Agent Reach collects intelligence (evidence)
                </p>
                <p className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
                  Signals are qualified by type + confidence
                </p>
                <p className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
                  Account priority scored (intent + CRM boost)
                </p>
                <p className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
                  Next Best Action generated per account
                </p>
                <p className="flex items-start gap-2">
                  <ArrowRight className="w-3 h-3 mt-0.5 shrink-0" />
                  Actions shown here with evidence trail
                </p>
              </div>
            </div>

            {analytics && (
              <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
                <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                  Feedback Metrics
                </h3>
                <div className="space-y-3 text-xs">
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Acceptance Rate</span>
                    <span className="font-medium text-[var(--text-primary)]">{(analytics.acceptance_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Conversion Rate</span>
                    <span className="font-medium text-[var(--text-primary)]">{(analytics.conversion_rate * 100).toFixed(0)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Avg Time-to-Action</span>
                    <span className="font-medium text-[var(--text-primary)]">{analytics.avg_hours_to_action.toFixed(1)}h</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-[var(--text-muted)]">Total Feedback</span>
                    <span className="font-medium text-[var(--text-primary)]">{analytics.total_feedback}</span>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
