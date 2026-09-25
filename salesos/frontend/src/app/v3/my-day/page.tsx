"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  RefreshCw, Phone, Mail, MessageSquare, Calendar, Target, FileText,
  Clock, CheckCircle2, TrendingUp, Zap, Brain, ArrowRight,
  ThumbsDown, HelpCircle,
} from "lucide-react";
import { PageHeader } from "../_components/page-header";
import { EmptyState, ErrorState, LoadingState, PermissionState } from "../_components/states";
import { useAccessToken } from "../_hooks/useAccessToken";
import { getTenantId } from "@/lib/hooks/useTenant";
import { hitlKeys } from "@/lib/queryKeys";
import { getMyDay, recordFeedback, completeFollowup, type WorkQueue } from "@/lib/api/hitl";
import { track } from "@/lib/analytics";
import SellerGuidance from "@/components/v3/seller-guidance";

const ACTION_ICONS: Record<string, typeof Phone> = {
  call: Phone, email: Mail, whatsapp: MessageSquare, meeting: Calendar,
  create_opportunity: Target, proposal: FileText, follow_up: Clock,
  research: Brain, no_action: Clock,
};

const ACTION_COLORS: Record<string, string> = {
  call: "text-orange-600", email: "text-blue-600", whatsapp: "text-emerald-600",
  meeting: "text-purple-600", create_opportunity: "text-amber-600",
  proposal: "text-indigo-600", follow_up: "text-gray-600", research: "text-teal-600",
  no_action: "text-gray-400",
};

function ActionIcon({ type }: { type: string }) {
  const Icon = ACTION_ICONS[type] || Clock;
  const color = ACTION_COLORS[type] || "text-gray-600";
  return <Icon className={`w-4 h-4 ${color}`} />;
}

function formatTimeAgo(dateStr: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

function formatDue(dueStr: string): string {
  const due = new Date(dueStr);
  const now = new Date();
  const diff = due.getTime() - now.getTime();
  const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
  if (days < 0) return `${Math.abs(days)}d overdue`;
  if (days === 0) return "Due today";
  if (days === 1) return "Due tomorrow";
  return `Due in ${days}d`;
}

function ActionCard({ workQueue }: { workQueue: WorkQueue }) {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();
  const [rejectingActionId, setRejectingActionId] = useState<string | null>(null);

  const acceptMutation = useMutation({
    mutationFn: async (actionId: string) => {
      return recordFeedback({
        action_id: actionId,
        recommendation_id: actionId,
        company_name: workQueue.pending_actions.find((a) => a.id === actionId)?.company_name || "",
        decision: "accepted",
        original_action_type: workQueue.pending_actions.find((a) => a.id === actionId)?.action_type || "",
      }, tenantId);
    },
    onSuccess: (_result, actionId) => {
      const action = workQueue.pending_actions.find((candidate) => candidate.id === actionId);
      track({
        type: "nba.accepted",
        metadata: {
          actionId,
          recommendationId: actionId,
          actionType: action?.action_type,
          surface: "my_day",
        },
      });
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.feedback(action?.company_name || "") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: async ({ actionId, reasonCode }: { actionId: string; reasonCode: string }) => {
      const action = workQueue.pending_actions.find((candidate) => candidate.id === actionId);
      return recordFeedback({
        action_id: actionId,
        recommendation_id: actionId,
        company_name: action?.company_name || "",
        decision: "rejected",
        reason_code: reasonCode,
        notes: "Rejected from My Day",
        original_action_type: action?.action_type || "",
      }, tenantId);
    },
    onSuccess: (_result, { actionId, reasonCode }) => {
      const action = workQueue.pending_actions.find((candidate) => candidate.id === actionId);
      track({
        type: "nba.rejected",
        metadata: {
          actionId,
          recommendationId: actionId,
          actionType: action?.action_type,
          reasonCode,
          surface: "my_day",
        },
      });
      setRejectingActionId(null);
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.feedback(action?.company_name || "") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
    },
  });

  if (workQueue.pending_actions.length === 0) {
    return (
      <EmptyState
        title="No pending actions"
        description="All caught up! Actions will appear here when signals are detected."
      />
    );
  }

  return (
    <div className="space-y-2">
      {workQueue.pending_actions.map((action) => (
        <div key={action.id} className="flex items-start gap-3 p-4 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)]">
          <div className="mt-0.5">
            <ActionIcon type={action.action_type} />
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h4 className="text-sm font-medium text-[var(--text-primary)]">{action.company_name}</h4>
              <span className="text-[10px] px-1.5 py-0.5 rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] font-medium">
                {action.action_type.replace(/_/g, " ")}
              </span>
            </div>
            <p className="text-xs text-[var(--text-muted)] mt-0.5 line-clamp-2">{action.notes}</p>
            <div className="flex items-center gap-2 mt-2">
              <button
                onClick={() => acceptMutation.mutate(action.id)}
                className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:bg-[var(--border-primary)] border border-[var(--border-primary)] transition-colors"
              >
                <CheckCircle2 className="w-3 h-3" />
                Accept
              </button>
              <button
                onClick={() => setRejectingActionId(rejectingActionId === action.id ? null : action.id)}
                className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--border-primary)] border border-[var(--border-primary)] transition-colors"
              >
                <ThumbsDown className="w-3 h-3" />
                Reject
              </button>
            </div>
            {rejectingActionId === action.id && (
              <div className="mt-2 flex flex-wrap gap-1.5" aria-label="Select rejection reason">
                {[
                  ["wrong_person", "Wrong person"],
                  ["bad_timing", "Bad timing"],
                  ["not_relevant", "Not relevant"],
                  ["already_contacted", "Already contacted"],
                  ["budget_constraint", "Budget constraint"],
                  ["other", "Other"],
                ].map(([reasonCode, label]) => (
                  <button
                    key={reasonCode}
                    type="button"
                    disabled={rejectMutation.isPending}
                    onClick={() => rejectMutation.mutate({ actionId: action.id, reasonCode })}
                    className="rounded border border-[var(--border-primary)] px-2 py-1 text-[10px] text-[var(--text-muted)] hover:bg-[var(--bg-secondary)] disabled:opacity-50"
                  >
                    {label}
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex flex-col items-end gap-1">
            <span className="text-[10px] text-[var(--text-muted)]">{formatTimeAgo(action.created_at)}</span>
          </div>
        </div>
      ))}
    </div>
  );
}

function FollowupCard({ followup, onDone }: { followup: WorkQueue["pending_followups"][0]; onDone: () => void }) {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  const completeMutation = useMutation({
    mutationFn: async () => completeFollowup(followup.id, "completed", tenantId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      onDone();
    },
  });

  const isOverdue = new Date(followup.due_at) < new Date();

  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)]">
      <ActionIcon type={followup.generated_action_type} />
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium text-[var(--text-primary)]">{followup.title}</div>
        <div className="text-xs text-[var(--text-muted)] mt-0.5">{followup.description}</div>
        <div className="text-[10px] text-[var(--text-muted)] mt-1">{followup.rationale}</div>
      </div>
      <div className="flex flex-col items-end gap-1">
        <span className={`text-[10px] ${isOverdue ? "text-[var(--text-primary)] font-medium" : "text-[var(--text-muted)]"}`}>
          {formatDue(followup.due_at)}
        </span>
        <button
          onClick={() => completeMutation.mutate()}
          className="text-[var(--text-muted)] hover:text-[var(--text-primary)]"
          title="Mark done"
        >
          <CheckCircle2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

function MetricsBar({ workQueue }: { workQueue: WorkQueue }) {
  const s = workQueue.summary;
  return (
    <div className="grid grid-cols-4 gap-3 mb-6">
      {[
        { label: "Pending Actions", value: s.pending_actions, icon: Zap, color: "text-orange-600" },
        { label: "Follow-ups Due", value: s.pending_followups, icon: Clock, color: "text-blue-600" },
        { label: "Outcomes (7d)", value: s.outcomes_7d, icon: TrendingUp, color: "text-purple-600" },
        { label: "Connected (7d)", value: s.connected_7d, icon: Phone, color: "text-emerald-600" },
      ].map((m) => (
        <div key={m.label} className="flex items-center gap-3 p-3 rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)]">
          <m.icon className={`w-5 h-5 ${m.color}`} />
          <div>
            <div className="text-lg font-semibold text-[var(--text-primary)]">{m.value}</div>
            <div className="text-[11px] text-[var(--text-muted)] uppercase tracking-wide">{m.label}</div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function MyDayPage() {
  const { ready, hasToken } = useAccessToken();
  const [showGuidance, setShowGuidance] = useState(false);

  const { data: workQueue, isLoading, isError, error, refetch } = useQuery({
    queryKey: hitlKeys.myDay("current-user"),
    queryFn: () => getMyDay(getTenantId()),
    enabled: ready && hasToken,
    refetchInterval: 30000,
  });

  if (!ready) return <LoadingState label="Checking session…" />;
  if (!hasToken) return <PermissionState nextPath="/v3/my-day" />;
  if (isLoading) return <LoadingState label="Loading your day…" />;
  if (isError)
    return (
      <div className="min-h-screen">
        <PageHeader
          title="My Day"
          description="Your prioritized work queue - actions, follow-ups, and outcomes"
        />
        <div className="px-6">
          <ErrorState
            title="Could not load work queue"
            description={error instanceof Error ? error.message : "Request failed"}
            onRetry={() => void refetch()}
          />
        </div>
      </div>
    );

  const wq = workQueue ?? { pending_actions: [], pending_followups: [], recent_outcomes: [], summary: { pending_actions: 0, pending_followups: 0, outcomes_7d: 0, connected_7d: 0 } };

  return (
    <div className="min-h-screen">
      {showGuidance && <SellerGuidance onClose={() => setShowGuidance(false)} />}
      <PageHeader
        title="My Day"
        description="Your prioritized work queue - actions, follow-ups, and outcomes"
        actions={
          <div className="flex items-center gap-3">
            <button
              onClick={() => setShowGuidance(true)}
              className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]"
            >
              <HelpCircle className="w-3.5 h-3.5" /> Seller Guide
            </button>
            <button onClick={() => refetch()} className="inline-flex items-center gap-1.5 text-sm text-[var(--text-muted)] hover:text-[var(--text-primary)]">
              <RefreshCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>
        }
      />
      <div className="px-6 pb-8">
        <MetricsBar workQueue={wq} />
        <div className="grid grid-cols-3 gap-6">
          <div className="col-span-2 space-y-4">
            <h2 className="text-sm font-semibold text-[var(--text-primary)] uppercase tracking-wide">
              Pending Actions ({wq.pending_actions.length})
            </h2>
            <ActionCard workQueue={wq} />
          </div>
          <div className="space-y-6">
            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                Follow-ups Due ({wq.pending_followups.length})
              </h3>
              {wq.pending_followups.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No follow-ups due.</p>
              ) : (
                <div className="space-y-2">
                  {wq.pending_followups.map((fu) => (
                    <FollowupCard key={fu.id} followup={fu} onDone={() => refetch()} />
                  ))}
                </div>
              )}
            </div>
            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">
                Recent Outcomes (7d)
              </h3>
              {wq.recent_outcomes.length === 0 ? (
                <p className="text-sm text-[var(--text-muted)]">No outcomes logged yet.</p>
              ) : (
                <div className="space-y-1.5">
                  {wq.recent_outcomes.slice(0, 5).map((o) => (
                    <div key={o.id} className="flex items-center gap-2 text-xs">
                      <span className="text-[var(--text-muted)]">{formatTimeAgo(o.occurred_at)}</span>
                      <span className="text-[var(--text-primary)] font-medium">{o.company_name}</span>
                      <span className="text-[var(--text-muted)]">{o.outcome_type}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
            <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
              <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-3">How It Works</h3>
              <div className="space-y-2 text-xs text-[var(--text-muted)]">
                <p className="flex items-start gap-2"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> Accept = proceed with recommendation</p>
                <p className="flex items-start gap-2"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> Reject = skip (with reason)</p>
                <p className="flex items-start gap-2"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> Log outcome after action</p>
                <p className="flex items-start gap-2"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> Follow-ups auto-generated from outcomes</p>
                <p className="flex items-start gap-2"><ArrowRight className="w-3 h-3 mt-0.5 shrink-0" /> Feedback loop improves recommendations</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
