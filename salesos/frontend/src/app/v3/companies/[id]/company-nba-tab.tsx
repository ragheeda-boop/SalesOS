"use client";

import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  ArrowRight, Brain, CheckCircle2, Clock, Mail, MessageSquare, Phone,
  Target, FileText, Calendar, ThumbsDown,
} from "lucide-react";
import { getTenantId } from "@/lib/hooks/useTenant";
import apiClient from "@/lib/api/client";
import {
  recordFeedback, recordOutcome,
  getCompanyFeedback, getCompanyOutcomes,
} from "@/lib/api/hitl";
import type { Opportunity } from "@/lib/api";
import { hitlKeys } from "@/lib/queryKeys";
import { track, useNbaExposureTracking } from "@/lib/analytics";

interface SalesAction {
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

interface AccountPriority {
  company_name: string;
  intent_level: string;
  intent_score: number;
  signal_count: number;
  critical_signals: number;
  recommended_action: string;
  action_urgency: string;
  metadata: Record<string, unknown>;
}

interface NextBestAction {
  id: string;
  company_name: string;
  action_type: string;
  urgency: string;
  title: string;
  description: string;
  rationale: string;
  confidence: number;
  expires_at: string;
  signals_used: string[];
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
  call: "text-orange-600 bg-[var(--bg-secondary)]",
  email: "text-blue-600 bg-[var(--bg-secondary)]",
  whatsapp: "text-emerald-600 bg-[var(--bg-secondary)]",
  meeting: "text-purple-600 bg-[var(--bg-secondary)]",
  create_opportunity: "text-amber-600 bg-[var(--bg-secondary)]",
  proposal: "text-indigo-600 bg-[var(--bg-secondary)]",
  follow_up: "text-[var(--text-muted)] bg-[var(--bg-secondary)]",
  research: "text-teal-600 bg-[var(--bg-secondary)]",
  no_action: "text-[var(--text-muted)] bg-[var(--bg-secondary)]",
};

const URGENCY_COLORS: Record<string, string> = {
  IMMEDIATE: "bg-[var(--bg-secondary)] text-[var(--text-primary)]",
  TODAY: "bg-[var(--bg-secondary)] text-[var(--text-primary)]",
  THIS_WEEK: "bg-[var(--bg-secondary)] text-[var(--text-muted)]",
  NEXT_WEEK: "bg-[var(--bg-secondary)] text-[var(--text-muted)]",
  MONITOR: "bg-[var(--bg-secondary)] text-[var(--text-muted)]",
};

const OUTCOME_OPTIONS = [
  { value: "connected", label: "Connected" },
  { value: "no_answer", label: "No Answer" },
  { value: "left_voicemail", label: "Voicemail" },
  { value: "email_sent", label: "Email Sent" },
  { value: "meeting_set", label: "Meeting Set" },
  { value: "positive", label: "Positive" },
  { value: "negative", label: "Negative" },
  { value: "neutral", label: "Neutral" },
  { value: "proposal_sent", label: "Proposal Sent" },
];

const REJECT_REASONS = [
  { value: "wrong_person", label: "Wrong Person" },
  { value: "bad_timing", label: "Bad Timing" },
  { value: "not_relevant", label: "Not Relevant" },
  { value: "already_contacted", label: "Already Contacted" },
  { value: "budget_constraint", label: "Budget Constraint" },
  { value: "other", label: "Other" },
];

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

function ExplainabilityBlock({ notes }: { notes: string }) {
  if (!notes) return null;
  const lines = notes.split(";").map((l) => l.trim()).filter(Boolean);
  return (
    <div className="rounded-md bg-[var(--bg-secondary)] p-3 space-y-1">
      <div className="text-[11px] font-semibold text-[var(--text-muted)] uppercase tracking-wide mb-1">
        Scoring Breakdown
      </div>
      {lines.map((line, i) => (
        <div key={i} className="text-xs text-[var(--text-secondary)] font-mono">
          {line}
        </div>
      ))}
    </div>
  );
}

function OutcomeForm({ actionId, companyId, companyName, opportunities, onSuccess }: {
  actionId: string;
  companyId: string;
  companyName: string;
  opportunities: Opportunity[];
  onSuccess: () => void;
}) {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();
  const [opportunityId, setOpportunityId] = useState("");
  // Keep a retry of this visible submission tied to the same server record.
  const [idempotencyKey] = useState(() => crypto.randomUUID());

  const mutation = useMutation({
    mutationFn: async (outcomeType: string) => {
      return recordOutcome({
        action_id: actionId,
        company_name: companyName,
        opportunity_id: opportunityId || undefined,
        idempotency_key: idempotencyKey,
        outcome_type: outcomeType,
        followup_required: true,
      }, tenantId);
    },
    onSuccess: (_result, outcomeType) => {
      track({
        type: "nba.outcome_recorded",
        companyId,
        metadata: { actionId, recommendationId: actionId, outcomeType, surface: "company_nba" },
      });
      queryClient.invalidateQueries({ queryKey: ["companyNba", companyName] });
      queryClient.invalidateQueries({ queryKey: hitlKeys.outcomes(companyName) });
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
      onSuccess();
    },
  });

  return (
    <div className="mt-2 space-y-2">
      {opportunities.length > 0 && (
        <label className="block text-[11px] text-[var(--text-muted)]">
          Link to opportunity (optional)
          <select
            aria-label="Link outcome to opportunity"
            value={opportunityId}
            onChange={(event) => setOpportunityId(event.target.value)}
            disabled={mutation.isPending}
            className="mt-1 block w-full max-w-sm rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] px-2 py-1 text-xs text-[var(--text-primary)]"
          >
            <option value="">No opportunity linked</option>
            {opportunities.map((opportunity) => (
              <option key={opportunity.id} value={opportunity.id}>
                {opportunity.name} · {opportunity.stage}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="flex flex-wrap gap-1.5">
        {OUTCOME_OPTIONS.map((opt) => (
          <button
            key={opt.value}
            onClick={() => mutation.mutate(opt.value)}
            disabled={mutation.isPending}
            className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] transition-colors"
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function RejectForm({ actionId, companyId, companyName, onSuccess }: {
  actionId: string; companyId: string; companyName: string; onSuccess: () => void;
}) {
  const queryClient = useQueryClient();
  const tenantId = getTenantId();

  const mutation = useMutation({
    mutationFn: async (reasonCode: string) => {
      return recordFeedback({
        action_id: actionId,
        recommendation_id: actionId,
        company_name: companyName,
        decision: "rejected",
        reason_code: reasonCode,
        original_action_type: "",
      }, tenantId);
    },
    onSuccess: (_result, reasonCode) => {
      track({
        type: "nba.rejected",
        companyId,
        metadata: { actionId, recommendationId: actionId, reasonCode, surface: "company_nba" },
      });
      queryClient.invalidateQueries({ queryKey: ["companyNba", companyName] });
      queryClient.invalidateQueries({ queryKey: hitlKeys.feedback(companyName) });
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
      onSuccess();
    },
  });

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {REJECT_REASONS.map((r) => (
        <button
          key={r.value}
          onClick={() => mutation.mutate(r.value)}
          disabled={mutation.isPending}
          className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded border border-[var(--border-primary)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] text-[var(--text-secondary)] transition-colors"
        >
          {r.label}
        </button>
      ))}
    </div>
  );
}

export function CompanyNbaTab({
  companyId,
  companyName,
  opportunities = [],
}: {
  companyId: string;
  companyName: string;
  opportunities?: Opportunity[];
}) {
  const queryClient = useQueryClient();
  const [showScore, setShowScore] = useState(false);
  const [rejectActionId, setRejectActionId] = useState<string | null>(null);
  const [outcomeActionId, setOutcomeActionId] = useState<string | null>(null);
  const tenantId = getTenantId();

  const { data: actions, isLoading: actionsLoading, isError: actionsError } = useQuery({
    queryKey: ["companyNba", companyName, "actions"],
    queryFn: async () => {
      const res = await apiClient.get("/api/v1/signal-actions/actions", {
        params: { company: companyName, status: "pending" },
        headers: { "X-Tenant-Id": tenantId },
      });
      const payload: unknown = res.data;
      if (Array.isArray(payload)) return payload as SalesAction[];
      if (
        payload &&
        typeof payload === "object" &&
        Array.isArray((payload as { actions?: unknown }).actions)
      ) {
        return (payload as { actions: SalesAction[] }).actions;
      }
      throw new Error("Unexpected sales actions response");
    },
  });

  const { data: scoreResult, isLoading: scoreLoading } = useQuery({
    queryKey: ["companyNba", companyName, "score"],
    queryFn: async () => {
      const res = await apiClient.post("/api/v1/signal-actions/score", {
        company_name: companyName,
      }, {
        headers: { "X-Tenant-Id": tenantId },
      });
      return res.data as { priority: AccountPriority; nba: NextBestAction };
    },
    enabled: showScore,
  });

  const { data: feedbackHistory } = useQuery({
    queryKey: hitlKeys.feedback(companyName),
    queryFn: () => getCompanyFeedback(companyName, tenantId),
  });

  const { data: outcomeHistory } = useQuery({
    queryKey: hitlKeys.outcomes(companyName),
    queryFn: () => getCompanyOutcomes(companyName, tenantId),
  });

  const acceptMutation = useMutation({
    mutationFn: async (actionId: string) => {
      return recordFeedback({
        action_id: actionId,
        recommendation_id: actionId,
        company_name: companyName,
        decision: "accepted",
        original_action_type: actions?.find((a) => a.id === actionId)?.action_type || "",
      }, tenantId);
    },
    onSuccess: (_result, actionId) => {
      track({
        type: "nba.accepted",
        companyId,
        metadata: { actionId, recommendationId: actionId, surface: "company_nba" },
      });
      queryClient.invalidateQueries({ queryKey: hitlKeys.feedback(companyName) });
      queryClient.invalidateQueries({ queryKey: ["companyNba", companyName] });
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
    },
  });

  const completeMutation = useMutation({
    mutationFn: async (actionId: string) => {
      await apiClient.post("/api/v1/signal-actions/complete", {
        action_id: actionId,
        outcome: "positive",
        notes: "Completed from Company 360",
      }, {
        headers: { "X-Tenant-Id": tenantId },
      });
    },
    onSuccess: (_result, actionId) => {
      track({
        type: "nba.executed",
        companyId,
        metadata: { actionId, recommendationId: actionId, surface: "company_nba" },
      });
      queryClient.invalidateQueries({ queryKey: ["companyNba", companyName] });
      queryClient.invalidateQueries({ queryKey: hitlKeys.myDay("current-user") });
      queryClient.invalidateQueries({ queryKey: hitlKeys.analytics() });
    },
  });

  const pendingActions = actions ?? [];
  useNbaExposureTracking(
    companyId,
    pendingActions.map((action) => ({ id: action.id, action: action.action_type })),
    !actionsLoading && !actionsError && pendingActions.length > 0,
  );
  const priority = scoreResult?.priority;
  const nba = scoreResult?.nba;
  const fbCount = feedbackHistory?.count ?? 0;
  const outCount = outcomeHistory?.count ?? 0;

  return (
    <div className="space-y-4">
      {/* Score Button + Result */}
      {!showScore ? (
        <button
          onClick={() => setShowScore(true)}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-medium rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] hover:bg-[var(--bg-secondary)] text-[var(--text-primary)] transition-colors"
        >
          <Brain className="w-4 h-4" />
          Score This Account
        </button>
      ) : scoreLoading ? (
        <div className="p-4 text-sm text-[var(--text-muted)]">Scoring...</div>
      ) : priority && nba ? (
        <div className="space-y-3">
          {/* Intent Score */}
          <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
            <div className="flex items-center justify-between mb-3">
              <h3 className="text-sm font-semibold text-[var(--text-primary)]">Intent Score</h3>
              <span className={`text-xs px-2 py-0.5 rounded font-medium ${URGENCY_COLORS[priority.action_urgency] || "bg-[var(--bg-secondary)] text-[var(--text-muted)]"}`}>
                {priority.action_urgency}
              </span>
            </div>
            <div className="flex items-baseline gap-2 mb-3">
              <span className="text-3xl font-bold text-[var(--text-primary)]">{priority.intent_score}</span>
              <span className="text-sm text-[var(--text-muted)]">/ 100</span>
              <span className="text-sm text-[var(--text-muted)] ml-2">
                ({priority.signal_count} signals, {priority.critical_signals} critical)
              </span>
            </div>
            {/* NBA */}
            <div className="flex items-center gap-3 p-3 rounded-md bg-[var(--bg-secondary)]">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center ${ACTION_COLORS[nba.action_type] || "bg-[var(--bg-secondary)] text-[var(--text-muted)]"}`}>
                {(() => { const I = ACTION_ICONS[nba.action_type] || Clock; return <I className="w-4 h-4" />; })()}
              </div>
              <div className="flex-1">
                <div className="text-sm font-medium text-[var(--text-primary)]">{nba.title}</div>
                <div className="text-xs text-[var(--text-muted)]">{nba.description}</div>
              </div>
              <ArrowRight className="w-4 h-4 text-[var(--text-muted)]" />
            </div>
          </div>

          {/* Rationale */}
          <ExplainabilityBlock notes={nba.rationale} />
        </div>
      ) : null}

      {/* HITL Stats */}
      <div className="flex gap-3 text-xs text-[var(--text-muted)]">
        <span>{fbCount} feedback</span>
        <span>{outCount} outcomes</span>
      </div>

      {/* Pending Actions */}
      <div>
        <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
          Pending Actions ({pendingActions.length})
        </h3>
        {actionsLoading ? (
          <p className="text-sm text-[var(--text-muted)]">Loading pending actions…</p>
        ) : actionsError ? (
          <p role="alert" className="text-sm text-[var(--text-muted)]">Could not load pending actions.</p>
        ) : pendingActions.length === 0 ? (
          <p className="text-sm text-[var(--text-muted)]">No pending actions for this company.</p>
        ) : (
          <div className="space-y-2">
            {pendingActions.map((action) => {
              const Icon = ACTION_ICONS[action.action_type] || Clock;
              const color = ACTION_COLORS[action.action_type] || "bg-[var(--bg-secondary)] text-[var(--text-muted)]";
              const isRejectOpen = rejectActionId === action.id;
              const isOutcomeOpen = outcomeActionId === action.id;
              return (
                <div key={action.id} className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-3">
                  <div className="flex items-center gap-3">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${color}`}>
                      <Icon className="w-4 h-4" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="text-sm font-medium text-[var(--text-primary)]">{formatActionType(action.action_type)}</div>
                      <div className="text-xs text-[var(--text-muted)] line-clamp-1">{action.notes}</div>
                    </div>
                    <span className="text-[10px] text-[var(--text-muted)]">{formatTimeAgo(action.created_at)}</span>
                  </div>
                  {/* Feedback buttons */}
                  <div className="flex items-center gap-2 mt-2">
                    <button
                      onClick={() => acceptMutation.mutate(action.id)}
                      disabled={acceptMutation.isPending}
                      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--bg-secondary)] text-[var(--text-primary)] hover:bg-[var(--border-primary)] border border-[var(--border-primary)] transition-colors"
                    >
                      <CheckCircle2 className="w-3 h-3" />
                      Accept
                    </button>
                    <button
                      onClick={() => { setRejectActionId(isRejectOpen ? null : action.id); setOutcomeActionId(null); }}
                      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--border-primary)] border border-[var(--border-primary)] transition-colors"
                    >
                      <ThumbsDown className="w-3 h-3" />
                      Reject
                    </button>
                    <button
                      onClick={() => { setOutcomeActionId(isOutcomeOpen ? null : action.id); setRejectActionId(null); }}
                      className="inline-flex items-center gap-1 px-2 py-1 text-[11px] rounded bg-[var(--bg-secondary)] text-[var(--text-muted)] hover:bg-[var(--border-primary)] border border-[var(--border-primary)] transition-colors"
                    >
                      Log Outcome
                    </button>
                    <button
                      onClick={() => completeMutation.mutate(action.id)}
                      disabled={completeMutation.isPending}
                      className="text-[var(--text-muted)] hover:text-[var(--text-primary)] ml-auto"
                      title="Mark completed"
                    >
                      <CheckCircle2 className="w-4 h-4" />
                    </button>
                  </div>
                  {/* Inline forms */}
                  {isRejectOpen && (
                    <RejectForm actionId={action.id} companyId={companyId} companyName={companyName} onSuccess={() => setRejectActionId(null)} />
                  )}
                  {isOutcomeOpen && (
                    <OutcomeForm
                      actionId={action.id}
                      companyId={companyId}
                      companyName={companyName}
                      opportunities={opportunities}
                      onSuccess={() => setOutcomeActionId(null)}
                    />
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Recent Feedback */}
      {fbCount > 0 && (
        <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
            Feedback History ({fbCount})
          </h3>
          <div className="space-y-1.5">
            {(feedbackHistory?.feedback ?? []).slice(0, 5).map((fb) => (
              <div key={fb.id} className="flex items-center gap-2 text-xs">
                <span className="text-[var(--text-muted)]">{formatTimeAgo(fb.created_at)}</span>
                <span className={`px-1.5 py-0.5 rounded text-[10px] font-medium ${
                  fb.decision === "accepted" ? "bg-[var(--bg-secondary)] text-[var(--text-primary)]"
                    : fb.decision === "rejected" ? "bg-[var(--bg-secondary)] text-[var(--text-muted)]"
                    : "bg-[var(--bg-secondary)] text-[var(--text-secondary)]"
                }`}>
                  {fb.decision}
                </span>
                {fb.reason_code && (
                  <span className="text-[var(--text-muted)]">({fb.reason_code})</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Recent Outcomes */}
      {outCount > 0 && (
        <div className="rounded-lg border border-[var(--border-primary)] bg-[var(--bg-primary)] p-4">
          <h3 className="text-sm font-semibold text-[var(--text-primary)] mb-2">
            Outcome History ({outCount})
          </h3>
          <div className="space-y-1.5">
            {(outcomeHistory?.outcomes ?? []).slice(0, 5).map((o) => (
              <div key={o.id} className="flex items-center gap-2 text-xs">
                <span className="text-[var(--text-muted)]">{formatTimeAgo(o.occurred_at)}</span>
                <span className="text-[var(--text-primary)] font-medium">{o.outcome_type}</span>
                {o.notes && <span className="text-[var(--text-muted)] line-clamp-1">{o.notes}</span>}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
