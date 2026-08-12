"use client";

import { useState, useCallback, useMemo } from "react";
import Link from "next/link";
import {
  useDecisionCenterList,
  useDecisionExplain,
  useDecisionFeedback,
  useDecisionFeedbackStats,
} from "@/lib/decisionQueries";
import { useTranslation } from "@/lib/i18n";
import {
  DataTable,
  Badge,
  Button,
  Card,
  Select,
  Modal,
  ModalContent,
  ModalHeader,
  ModalBody,
  ModalFooter,
  Skeleton,
  EmptyState,
  Textarea,
  DatePicker,
  Tooltip,
  useToast,
  cn,
} from "@salesos/ui";
import {
  Brain,
  Check,
  X,
  ChevronUp,
  ThumbsUp,
  ThumbsDown,
  MessageSquare,
  Zap,
  AlertTriangle,
  Filter,
  Search,
  RefreshCw,
  BarChart3,
  Settings,
  Eye,
} from "lucide-react";
import type { ColumnDef } from "@tanstack/react-table";
import { useQuery } from "@tanstack/react-query";
import api, { getCurrentUser } from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";
import { ExperimentalAiBadge } from "@/components/ai/ExperimentalAiBadge";

const DOMAIN_OPTIONS = [
  { label: "All Domains", value: "" },
  { label: "Company", value: "company" },
  { label: "Opportunity", value: "opportunity" },
  { label: "Scoring", value: "scoring" },
  { label: "Workflow", value: "workflow" },
  { label: "AI", value: "ai" },
  { label: "Timeline", value: "timeline" },
  { label: "CRM", value: "crm" },
];

const TYPE_OPTIONS = [
  { label: "All Types", value: "" },
  { label: "Next Best Action", value: "nba" },
  { label: "Risk Alert", value: "risk_alert" },
  { label: "Upsell", value: "upsell" },
  { label: "Engagement", value: "engagement" },
  { label: "Churn Warning", value: "churn_warning" },
];

const STATUS_OPTIONS = [
  { label: "All", value: "" },
  { label: "Pending", value: "pending" },
  { label: "Accepted", value: "accepted" },
  { label: "Executed", value: "executed" },
  { label: "Dismissed", value: "dismissed" },
];

const DOMAIN_VARIANT: Record<string, "success" | "warning" | "danger" | "default" | "primary"> = {
  company: "primary",
  opportunity: "success",
  scoring: "warning",
  workflow: "default",
  ai: "danger",
  timeline: "primary",
  crm: "success",
};

const STATUS_VARIANT: Record<string, "success" | "warning" | "danger" | "default" | "primary"> = {
  pending: "warning",
  accepted: "success",
  executed: "primary",
  dismissed: "danger",
};

interface DecisionItem {
  id: string;
  entity_type: string;
  entity_id: string;
  action: string;
  priority: "high" | "medium" | "low";
  score: number;
  reasoning: string;
  created_at: string;
  status: "pending" | "accepted" | "executed" | "dismissed";
  domain?: string;
  type?: string;
  provider?: string;
  confidence?: number;
}

function ConfidenceGauge({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color =
    pct >= 80
      ? "text-[var(--status-success-text)]"
      : pct >= 50
        ? "text-yellow-600"
        : "text-[var(--status-danger-text)]";
  return (
    <div className="flex items-center gap-2">
      <div className="h-1.5 w-16 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
        <div
          className={cn(
            "h-full rounded-full",
            pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500"
          )}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn("text-xs font-medium", color)}>{pct}%</span>
    </div>
  );
}

function formatDate(dateStr: string): string {
  try {
    return new Intl.DateTimeFormat("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(new Date(dateStr));
  } catch {
    return dateStr;
  }
}

function AuditTrailPanel({ decisionId, onClose }: { decisionId: string; onClose: () => void }) {
  const { t } = useTranslation();
  const { data: audit, isLoading } = useDecisionExplain(decisionId);

  if (isLoading) {
    return (
      <div className="space-y-3 p-4">
        <Skeleton className="h-5 w-48" />
        <Skeleton className="h-4 w-full" />
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
      </div>
    );
  }

  return (
    <div className="border-t border-[var(--border-default)] bg-[var(--bg-secondary)]/50 p-4 space-y-4">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-semibold text-[var(--text-primary)]">
          {t("decisions.audit_trail")}
        </h4>
        <button
          onClick={onClose}
          className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      {audit ? (
        <div className="space-y-4">
          {audit.summary && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                {t("decisions.summary")}
              </p>
              <p className="text-sm text-[var(--text-secondary)]">{audit.summary}</p>
            </div>
          )}

          {audit.factors && audit.factors.length > 0 && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] mb-2">
                {t("decisions.confidence_factors")}
              </p>
              <div className="space-y-2">
                {audit.factors.map((f, i) => (
                  <div key={i} className="flex items-center gap-3">
                    <span className="text-sm text-[var(--text-secondary)] min-w-[120px]">
                      {f.name}
                    </span>
                    <div className="flex-1 h-1.5 rounded-full bg-[var(--bg-tertiary)] overflow-hidden">
                      <div
                        className={cn(
                          "h-full rounded-full",
                          f.impact === "high"
                            ? "bg-red-500"
                            : f.impact === "medium"
                              ? "bg-yellow-500"
                              : "bg-green-500"
                        )}
                        style={{
                          width: `${Math.round((f.value ?? 0) * 100)}%`,
                        }}
                      />
                    </div>
                    <span className="text-xs text-[var(--text-muted)] w-10 text-right">
                      {Math.round((f.value ?? 0) * 100)}%
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {audit.why && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                {t("decisions.why")}
              </p>
              <p className="text-sm text-[var(--text-secondary)]">{audit.why}</p>
            </div>
          )}

          {audit.expectedImpact && (
            <div>
              <p className="text-xs font-medium text-[var(--text-muted)] mb-1">
                {t("decisions.expected_impact")}
              </p>
              <p className="text-sm text-[var(--text-secondary)]">{audit.expectedImpact}</p>
            </div>
          )}
        </div>
      ) : (
        <p className="text-sm text-[var(--text-muted)]">{t("decisions.no_audit_data")}</p>
      )}
    </div>
  );
}

function FeedbackModal({
  open,
  onClose,
  decisionId,
  onSubmitted,
}: {
  open: boolean;
  onClose: () => void;
  decisionId: string;
  onSubmitted: () => void;
}) {
  const { t } = useTranslation();
  const { toast } = useToast();
  const [outcome, setOutcome] = useState<"accepted" | "rejected" | "ignored">("accepted");
  const [reason, setReason] = useState("");
  const [revenueImpact, setRevenueImpact] = useState("");

  const submitFeedback = useDecisionFeedback();

  const handleSubmit = useCallback(async () => {
    try {
      await submitFeedback.mutateAsync({
        decisionId,
        outcome,
        reason: reason || undefined,
        revenueImpact: revenueImpact ? Number(revenueImpact) : undefined,
      });
      toast({ variant: "success", title: t("decisions.feedback_submitted") });
      onSubmitted();
      onClose();
      setReason("");
      setRevenueImpact("");
    } catch {
      toast({ variant: "error", title: t("decisions.feedback_failed") });
    }
  }, [decisionId, outcome, reason, revenueImpact, submitFeedback, toast, t, onSubmitted, onClose]);

  return (
    <Modal open={open} onOpenChange={onClose}>
      <ModalContent>
        <ModalHeader>{t("decisions.submit_feedback")}</ModalHeader>
        <ModalBody>
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-[var(--text-secondary)] mb-3">
                {t("decisions.feedback_question")}
              </p>
              <div className="flex gap-3">
                {[
                  {
                    value: "accepted" as const,
                    icon: ThumbsUp,
                    label: t("decisions.accept"),
                    color:
                      "text-[var(--status-success-text)] border-green-300 hover:bg-[var(--status-success-bg)] dark:hover:bg-green-900/20",
                  },
                  {
                    value: "rejected" as const,
                    icon: ThumbsDown,
                    label: t("decisions.reject"),
                    color:
                      "text-[var(--status-danger-text)] border-red-300 hover:bg-[var(--status-danger-bg)] dark:hover:bg-red-900/20",
                  },
                  {
                    value: "ignored" as const,
                    icon: X,
                    label: t("decisions.ignore"),
                    color:
                      "text-[var(--text-secondary)] border-[var(--border-hover)] hover:bg-[var(--bg-secondary)] dark:hover:bg-[var(--bg-secondary)]",
                  },
                ].map((opt) => (
                  <button
                    key={opt.value}
                    onClick={() => setOutcome(opt.value)}
                    className={cn(
                      "flex items-center gap-2 rounded-lg border-2 px-4 py-3 text-sm font-medium transition-all",
                      outcome === opt.value
                        ? opt.color
                        : "border-[var(--border-default)] text-[var(--text-muted)]"
                    )}
                  >
                    <opt.icon className="h-4 w-4" />
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                {t("decisions.reason")} ({t("common.optional")})
              </label>
              <Textarea
                placeholder={t("decisions.reason_placeholder")}
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                rows={3}
                resize="vertical"
              />
            </div>

            <div>
              <label className="mb-1 block text-sm font-medium text-[var(--text-secondary)]">
                {t("decisions.revenue_impact")} ({t("common.optional")})
              </label>
              <input
                type="number"
                placeholder="e.g. 50000"
                value={revenueImpact}
                onChange={(e) => setRevenueImpact(e.target.value)}
                className="w-full rounded-lg border border-[var(--border-hover)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
              />
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button variant="outline" onClick={onClose}>
            {t("common.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={submitFeedback.isPending}
            leftIcon={
              submitFeedback.isPending ? <RefreshCw className="h-4 w-4 animate-spin" /> : undefined
            }
          >
            {submitFeedback.isPending ? t("common.saving") : t("decisions.submit_feedback")}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  );
}

export default function DecisionCenterPage() {
  const { t } = useTranslation();
  const { toast } = useToast();

  const [searchQuery, setSearchQuery] = useState("");
  const [domainFilter, setDomainFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [confidenceMin, setConfidenceMin] = useState("");
  const [confidenceMax, setConfidenceMax] = useState("");
  const [dateFrom, setDateFrom] = useState<Date | null>(null);
  const [dateTo, setDateTo] = useState<Date | null>(null);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [expandedRow, setExpandedRow] = useState<string | null>(null);
  const [feedbackModalOpen, setFeedbackModalOpen] = useState(false);
  const [feedbackTarget, setFeedbackTarget] = useState<string | null>(null);

  const tenantId = getTenantId();

  // CTO window P1 (2026-08-08): honesty banners admin/owner only — not end-user chrome.
  const { data: currentUser } = useQuery({
    queryKey: ["profile", "me"],
    queryFn: getCurrentUser,
    staleTime: 5 * 60 * 1000,
  });
  const showHonestyBanner =
    currentUser?.role === "admin" || currentUser?.role === "owner";

  const { data, isLoading, isError, error, refetch } = useDecisionCenterList(50);

  const feedbackStats = useDecisionFeedbackStats();

  const decisions = useMemo(() => {
    if (!data?.items) return [];
    let items = data.items;

    if (searchQuery) {
      const q = searchQuery.toLowerCase();
      items = items.filter(
        (d) =>
          d.action?.toLowerCase().includes(q) ||
          d.entity_id?.toLowerCase().includes(q) ||
          d.reasoning?.toLowerCase().includes(q)
      );
    }
    if (domainFilter)
      items = items.filter((d) => d.domain === domainFilter || d.entity_type === domainFilter);
    if (typeFilter) items = items.filter((d) => d.type === typeFilter);
    if (statusFilter) items = items.filter((d) => d.status === statusFilter);
    if (confidenceMin)
      items = items.filter((d) => (d.confidence ?? d.score ?? 0) >= Number(confidenceMin) / 100);
    if (confidenceMax)
      items = items.filter((d) => (d.confidence ?? d.score ?? 0) <= Number(confidenceMax) / 100);
    if (dateFrom) items = items.filter((d) => new Date(d.created_at) >= dateFrom);
    if (dateTo) items = items.filter((d) => new Date(d.created_at) <= dateTo);

    return items;
  }, [
    data,
    searchQuery,
    domainFilter,
    typeFilter,
    statusFilter,
    confidenceMin,
    confidenceMax,
    dateFrom,
    dateTo,
  ]);

  const totalPages = useMemo(
    () => Math.max(1, Math.ceil(decisions.length / pageSize)),
    [decisions.length, pageSize]
  );
  const pagedDecisions = useMemo(() => {
    const start = (page - 1) * pageSize;
    return decisions.slice(start, start + pageSize);
  }, [decisions, page, pageSize]);

  const activeFilterCount = useMemo(
    () =>
      [
        domainFilter,
        typeFilter,
        statusFilter,
        confidenceMin,
        confidenceMax,
        dateFrom,
        dateTo,
      ].filter(Boolean).length,
    [domainFilter, typeFilter, statusFilter, confidenceMin, confidenceMax, dateFrom, dateTo]
  );

  const clearFilters = useCallback(() => {
    setSearchQuery("");
    setDomainFilter("");
    setTypeFilter("");
    setStatusFilter("");
    setConfidenceMin("");
    setConfidenceMax("");
    setDateFrom(null);
    setDateTo(null);
    setPage(1);
  }, []);

  const handleAccept = useCallback(
    async (id: string) => {
      try {
        // Center feedback only — no accept endpoint; status stays active until a human status API exists.
        await api.post(
          `/api/v1/decisions/${id}/feedback`,
          { rating: "up" },
          { headers: { "X-Tenant-Id": tenantId } }
        );
        toast({ variant: "success", title: t("decisions.accepted") });
        refetch();
      } catch {
        toast({ variant: "error", title: t("decisions.action_failed") });
      }
    },
    [refetch, toast, t, tenantId]
  );

  const handleDismiss = useCallback(
    async (id: string) => {
      try {
        await api.post(
          `/api/v1/decisions/${id}/feedback`,
          { rating: "down" },
          { headers: { "X-Tenant-Id": tenantId } }
        );
        toast({ variant: "success", title: t("decisions.dismissed") });
        refetch();
      } catch {
        toast({ variant: "error", title: t("decisions.action_failed") });
      }
    },
    [refetch, toast, t, tenantId]
  );

  const openFeedback = useCallback((id: string) => {
    setFeedbackTarget(id);
    setFeedbackModalOpen(true);
  }, []);

  const columns: ColumnDef<DecisionItem>[] = useMemo(
    () => [
      {
        accessorKey: "domain",
        header: t("decisions.domain"),
        cell: ({ row }) => {
          const domain = row.original.domain || row.original.entity_type || "unknown";
          return <Badge variant={DOMAIN_VARIANT[domain] || "default"}>{domain}</Badge>;
        },
        size: 110,
      },
      {
        accessorKey: "action",
        header: t("decisions.decision"),
        cell: ({ row }) => (
          <div className="max-w-[300px]">
            <p className="text-sm font-medium text-[var(--text-primary)] truncate">
              {row.original.action}
            </p>
            {row.original.reasoning && (
              <p className="text-xs text-[var(--text-muted)] truncate mt-0.5">
                {row.original.reasoning}
              </p>
            )}
          </div>
        ),
      },
      {
        accessorKey: "confidence",
        header: t("decisions.confidence"),
        cell: ({ row }) => (
          <ConfidenceGauge value={row.original.confidence ?? row.original.score ?? 0} />
        ),
        size: 120,
      },
      {
        accessorKey: "priority",
        header: t("decisions.priority"),
        cell: ({ row }) => {
          const p = row.original.priority;
          return (
            <Badge variant={p === "high" ? "danger" : p === "medium" ? "warning" : "default"}>
              {p}
            </Badge>
          );
        },
        size: 90,
      },
      {
        accessorKey: "status",
        header: t("labels.status"),
        cell: ({ row }) => {
          const s = row.original.status || "pending";
          return <Badge variant={STATUS_VARIANT[s] || "default"}>{s}</Badge>;
        },
        size: 100,
      },
      {
        accessorKey: "created_at",
        header: t("labels.date"),
        cell: ({ row }) => (
          <Tooltip content={row.original.created_at}>
            <span className="text-xs text-[var(--text-muted)] whitespace-nowrap">
              {formatDate(row.original.created_at)}
            </span>
          </Tooltip>
        ),
        size: 140,
      },
      {
        id: "actions",
        header: "",
        cell: ({ row }) => {
          const d = row.original;
          return (
            <div className="flex items-center gap-1">
              <Tooltip content={t("decisions.view_audit")}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    setExpandedRow(expandedRow === d.id ? null : d.id);
                  }}
                  className="rounded p-1 text-[var(--text-disabled)] hover:text-[var(--muhide-orange)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  {expandedRow === d.id ? (
                    <ChevronUp className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </button>
              </Tooltip>
              <Tooltip content={t("decisions.give_feedback")}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    openFeedback(d.id);
                  }}
                  className="rounded p-1 text-[var(--text-disabled)] hover:text-[var(--muhide-orange)] hover:bg-[var(--bg-tertiary)] dark:hover:bg-[var(--bg-secondary)] transition-colors"
                >
                  <MessageSquare className="h-4 w-4" />
                </button>
              </Tooltip>
              {d.status === "pending" && (
                <>
                  <Tooltip content={t("decisions.accept")}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleAccept(d.id);
                      }}
                      className="rounded p-1 text-[var(--text-disabled)] hover:text-[var(--status-success-text)] hover:bg-[var(--status-success-bg)] transition-colors"
                    >
                      <Check className="h-4 w-4" />
                    </button>
                  </Tooltip>
                  <Tooltip content={t("decisions.dismiss")}>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        handleDismiss(d.id);
                      }}
                      className="rounded p-1 text-[var(--text-disabled)] hover:text-[var(--status-danger-text)] hover:bg-[var(--status-danger-bg)] transition-colors"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </Tooltip>
                </>
              )}
            </div>
          );
        },
        size: 140,
      },
    ],
    [t, expandedRow, handleAccept, handleDismiss, openFeedback]
  );

  if (isError) {
    return (
      <div className="p-6">
        <EmptyState
          icon={<AlertTriangle className="h-10 w-10 text-[var(--status-danger-text)]" />}
          title={t("decisions.load_error")}
          description={(error as Error)?.message || t("decisions.check_server")}
          action={{ label: t("common.retry"), onClick: () => refetch() }}
        />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-2xl font-bold text-[var(--text-primary)]">{t("decisions.title")}</h1>
            <ExperimentalAiBadge />
          </div>
          <p className="mt-1 text-sm text-[var(--text-muted)]">{t("decisions.subtitle")}</p>
          {showHonestyBanner ? (
            <p
              className="mt-1 text-xs text-[var(--text-muted)]"
              data-testid="decisions-honesty-banner"
            >
              Ledger list = Decision Center /api/v1/decisions. Accept/dismiss =
              Center feedback (up→accepted, down→rejected). Evaluate/scores stay
              on Platform /api/v1/decision/*. Not FE STUB; not AI-native GA.
              Not Production GO / RAG GO.
            </p>
          ) : null}
        </div>
        <div className="flex items-center gap-3">
          <Link href="/decisions/templates">
            <Button variant="outline" leftIcon={<Settings className="h-4 w-4" />}>
              {t("decisions.templates")}
            </Button>
          </Link>
          <Button leftIcon={<Brain className="h-4 w-4" />} onClick={() => refetch()}>
            {t("decisions.evaluate_all")}
          </Button>
        </div>
      </div>

      {feedbackStats.data && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-[var(--status-info-bg)] p-2">
                <BarChart3 className="h-5 w-5 text-[var(--status-info-text)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">{t("decisions.total_decisions")}</p>
                <p className="text-lg font-bold text-[var(--text-primary)]">{data?.total || 0}</p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-[var(--status-success-bg)] p-2">
                <ThumbsUp className="h-5 w-5 text-[var(--status-success-text)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">{t("decisions.acceptance_rate")}</p>
                <p className="text-lg font-bold text-[var(--text-primary)]">
                  {Math.round((feedbackStats.data.acceptanceRate || 0) * 100)}%
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-[var(--chart-purple-bg)] dark:bg-[var(--bg-primary)]/30 p-2">
                <ThumbsDown className="h-5 w-5 text-[var(--chart-purple)] dark:text-[var(--chart-purple)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">{t("decisions.rejection_rate")}</p>
                <p className="text-lg font-bold text-[var(--text-primary)]">
                  {Math.round((feedbackStats.data.rejectionRate || 0) * 100)}%
                </p>
              </div>
            </div>
          </Card>
          <Card className="p-4">
            <div className="flex items-center gap-3">
              <div className="rounded-lg bg-[var(--muhide-orange)]/10 p-2">
                <Zap className="h-5 w-5 text-[var(--muhide-orange)]" />
              </div>
              <div>
                <p className="text-xs text-[var(--text-muted)]">{t("decisions.total_feedback")}</p>
                <p className="text-lg font-bold text-[var(--text-primary)]">
                  {feedbackStats.data.totalFeedback}
                </p>
              </div>
            </div>
          </Card>
        </div>
      )}

      <div className="space-y-3">
        <div className="flex flex-wrap gap-3">
          <div className="flex-1 min-w-[200px] relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--text-disabled)]" />
            <input
              type="text"
              placeholder={t("decisions.search_placeholder")}
              value={searchQuery}
              onChange={(e) => {
                setSearchQuery(e.target.value);
                setPage(1);
              }}
              className="w-full rounded-lg border border-[var(--border-hover)] bg-[var(--bg-primary)] pl-9 pr-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
            />
          </div>
          <div className="w-40">
            <Select
              options={DOMAIN_OPTIONS}
              placeholder={t("decisions.domain")}
              value={domainFilter}
              onChange={(v) => {
                setDomainFilter(v);
                setPage(1);
              }}
            />
          </div>
          <div className="w-40">
            <Select
              options={TYPE_OPTIONS}
              placeholder={t("decisions.type")}
              value={typeFilter}
              onChange={(v) => {
                setTypeFilter(v);
                setPage(1);
              }}
            />
          </div>
          <div className="w-36">
            <Select
              options={STATUS_OPTIONS}
              placeholder={t("labels.status")}
              value={statusFilter}
              onChange={(v) => {
                setStatusFilter(v);
                setPage(1);
              }}
            />
          </div>
          <div className="w-28">
            <input
              type="number"
              placeholder={t("decisions.confidence_min")}
              value={confidenceMin}
              onChange={(e) => {
                setConfidenceMin(e.target.value);
                setPage(1);
              }}
              min="0"
              max="100"
              className="w-full rounded-lg border border-[var(--border-hover)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
            />
          </div>
          <div className="w-28">
            <input
              type="number"
              placeholder={t("decisions.confidence_max")}
              value={confidenceMax}
              onChange={(e) => {
                setConfidenceMax(e.target.value);
                setPage(1);
              }}
              min="0"
              max="100"
              className="w-full rounded-lg border border-[var(--border-hover)] bg-[var(--bg-primary)] px-3 py-2 text-sm text-[var(--text-primary)] placeholder:text-[var(--text-disabled)] focus:outline-none focus:ring-2 focus:ring-[var(--muhide-orange)]"
            />
          </div>
          <div className="w-44">
            <DatePicker
              mode="single"
              placeholder={t("decisions.date_from")}
              value={dateFrom}
              onChange={(v) => {
                setDateFrom(v as Date | null);
                setPage(1);
              }}
            />
          </div>
          <div className="w-44">
            <DatePicker
              mode="single"
              placeholder={t("decisions.date_to")}
              value={dateTo}
              onChange={(v) => {
                setDateTo(v as Date | null);
                setPage(1);
              }}
            />
          </div>
        </div>

        {activeFilterCount > 0 && (
          <div className="flex flex-wrap items-center gap-2">
            <Filter className="h-3.5 w-3.5 text-[var(--text-disabled)]" />
            {domainFilter && (
              <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                Domain: {domainFilter}
                <button
                  onClick={() => {
                    setDomainFilter("");
                    setPage(1);
                  }}
                  className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {typeFilter && (
              <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                Type: {typeFilter}
                <button
                  onClick={() => {
                    setTypeFilter("");
                    setPage(1);
                  }}
                  className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {statusFilter && (
              <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                Status: {statusFilter}
                <button
                  onClick={() => {
                    setStatusFilter("");
                    setPage(1);
                  }}
                  className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {(confidenceMin || confidenceMax) && (
              <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                Confidence: {confidenceMin || "0"}%–{confidenceMax || "100"}%
                <button
                  onClick={() => {
                    setConfidenceMin("");
                    setConfidenceMax("");
                    setPage(1);
                  }}
                  className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            {(dateFrom || dateTo) && (
              <span className="inline-flex items-center gap-1 rounded-md bg-[var(--bg-tertiary)] px-2 py-1 text-xs text-[var(--text-secondary)]">
                Date: {dateFrom ? formatDate(dateFrom.toISOString()) : "..."} –{" "}
                {dateTo ? formatDate(dateTo.toISOString()) : "..."}
                <button
                  onClick={() => {
                    setDateFrom(null);
                    setDateTo(null);
                    setPage(1);
                  }}
                  className="text-[var(--text-disabled)] hover:text-[var(--text-secondary)] dark:hover:text-[var(--text-disabled)]"
                >
                  <X className="h-3 w-3" />
                </button>
              </span>
            )}
            <button
              onClick={clearFilters}
              className="text-xs text-[var(--muhide-orange)] hover:underline"
            >
              {t("decisions.clear_all")}
            </button>
          </div>
        )}
      </div>

      <div className="overflow-hidden rounded-xl border border-[var(--border-default)] bg-[var(--bg-primary)]">
        <DataTable<DecisionItem>
          columns={columns}
          data={pagedDecisions}
          loading={isLoading}
          emptyState={{
            icon: <Brain className="h-10 w-10" />,
            title:
              searchQuery || activeFilterCount > 0
                ? t("decisions.no_search_results")
                : t("decisions.empty"),
            description:
              searchQuery || activeFilterCount > 0
                ? t("decisions.try_different_search")
                : t("decisions.empty_hint"),
            ...(!searchQuery && activeFilterCount === 0
              ? {
                  action: {
                    label: t("decisions.evaluate_all"),
                    onClick: () => refetch(),
                  },
                }
              : {}),
          }}
        />

        {pagedDecisions.map(
          (d) =>
            expandedRow === d.id && (
              <AuditTrailPanel
                key={`audit-${d.id}`}
                decisionId={d.id}
                onClose={() => setExpandedRow(null)}
              />
            )
        )}
      </div>

      {decisions.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-sm text-[var(--text-muted)]">
            {t("decisions.pagination", {
              total: decisions.length,
              page: page,
              totalPages: totalPages,
            })}
          </p>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              {t("common.previous")}
            </Button>
            {Array.from({ length: Math.min(totalPages, 5) }, (_, i) => {
              const start = Math.max(1, Math.min(page - 2, totalPages - 4));
              const p = start + i;
              if (p > totalPages) return null;
              return (
                <Button
                  key={p}
                  variant={p === page ? "primary" : "outline"}
                  size="sm"
                  onClick={() => setPage(p)}
                >
                  {p}
                </Button>
              );
            })}
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              {t("common.next")}
            </Button>
          </div>
        </div>
      )}

      <FeedbackModal
        open={feedbackModalOpen}
        onClose={() => {
          setFeedbackModalOpen(false);
          setFeedbackTarget(null);
        }}
        decisionId={feedbackTarget || ""}
        onSubmitted={() => refetch()}
      />
    </div>
  );
}
