"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { decisionKeys } from "@/lib/queryKeys";
import { getTenantId } from "./hooks/useTenant";
import { asArray } from "@/lib/asArray";
import type {
  DecisionContext,
  DecisionResult,
  DecisionHistoryItem,
  Recommendation,
  Score,
  EvidenceItem,
  Feedback,
} from "@salesos/decision-platform";

// ─── Types ────────────────────────────────────────────────────
export interface DecisionEvaluateRequest {
  context: DecisionContext;
}

export interface DecisionFeedbackRequest {
  decisionId: string;
  outcome: "accepted" | "rejected" | "ignored";
  reason?: string;
  revenueImpact?: number;
  timeToExecution?: number;
  actualEffort?: string;
  metadata?: Record<string, unknown>;
}

export interface DecisionHistoryResponse {
  items: DecisionHistoryItem[];
  total: number;
}

/** Decision Center list row (camelCase OpenAPI) mapped for /decisions UI. */
export interface DecisionCenterLedgerItem {
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

export interface DecisionCenterListResponse {
  items: DecisionCenterLedgerItem[];
  total: number;
}

function mapCenterStatus(
  status: string | undefined
): DecisionCenterLedgerItem["status"] {
  if (status === "accepted" || status === "executed") return status;
  if (status === "rejected" || status === "expired" || status === "superseded" || status === "dismissed") {
    return "dismissed";
  }
  return "pending";
}

export function mapDecisionCenterItem(raw: Record<string, unknown>): DecisionCenterLedgerItem {
  const confidence = Number(raw.confidence ?? 0);
  const status = typeof raw.status === "string" ? raw.status : "active";
  return {
    id: String(raw.id ?? ""),
    entity_type: String(raw.entityType ?? raw.entity_type ?? ""),
    entity_id: String(raw.entityId ?? raw.entity_id ?? ""),
    action: String(raw.decision ?? raw.action ?? ""),
    priority: confidence >= 0.8 ? "high" : confidence >= 0.5 ? "medium" : "low",
    score: confidence,
    reasoning: String(raw.reasoning ?? ""),
    created_at: String(raw.timestamp ?? raw.created_at ?? ""),
    status: mapCenterStatus(status),
    domain: typeof raw.domain === "string" ? raw.domain : undefined,
    type: typeof raw.type === "string" ? raw.type : undefined,
    provider: typeof raw.provider === "string" ? raw.provider : undefined,
    confidence,
  };
}

export interface DecisionFeedbackStatsResponse {
  totalFeedback: number;
  acceptanceRate: number;
  rejectionRate: number;
  avgRevenueImpact: number;
  byAction: Record<string, { accepted: number; rejected: number; ignored: number }>;
}

// ─── Hooks ────────────────────────────────────────────────────
export function useDecisionEvaluate() {
  return useMutation<DecisionResult, Error, DecisionEvaluateRequest>({
    mutationFn: async ({ context }) => {
      const response = await api.post(
        "/api/v1/decision/evaluate",
        { context },
        {
          headers: { "X-Tenant-Id": getTenantId() },
        }
      );
      return response.data;
    },
  });
}

export function useDecisionExplain(decisionId: string) {
  return useQuery({
    queryKey: decisionKeys.explain(decisionId),
    queryFn: async () => {
      const response = await api.get(`/api/v1/decision/${decisionId}/explain`, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data as DecisionResult["explainability"];
    },
    enabled: !!decisionId,
    staleTime: 30_000,
  });
}

export function useDecisionHistory(limit?: number) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: [...decisionKeys.history(tenantId), { limit }],
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/history", {
        params: { limit },
        headers: { "X-Tenant-Id": tenantId },
      });
      return response.data as DecisionHistoryResponse;
    },
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
}

/** Governed ledger list — Decision Center SoT (`/api/v1/decisions`). */
export function useDecisionCenterList(limit?: number) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: [...decisionKeys.center(tenantId), { limit }],
    queryFn: async () => {
      const response = await api.get("/api/v1/decisions", {
        params: { limit: limit ?? 50 },
        headers: { "X-Tenant-Id": tenantId },
      });
      const payload = response.data as { items?: unknown; total?: number };
      const items = asArray<Record<string, unknown>>(payload?.items ?? payload).map(
        mapDecisionCenterItem
      );
      return {
        items,
        total: typeof payload?.total === "number" ? payload.total : items.length,
      } satisfies DecisionCenterListResponse;
    },
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
}

export function useDecisionRecommendations(entityId?: string, entityType?: string) {
  return useQuery({
    queryKey: [...decisionKeys.recommendations(entityId), { entityType }],
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/recommendations", {
        params: { entity_id: entityId, entity_type: entityType },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return asArray<Recommendation>(response.data);
    },
    staleTime: 15_000,
    refetchInterval: 60_000,
  });
}

export function useDecisionScores(entityId: string, entityType: string) {
  return useQuery({
    queryKey: decisionKeys.scores(entityId),
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/scores", {
        params: { entity_id: entityId, entity_type: entityType },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return asArray<Score>(response.data);
    },
    enabled: !!entityId && !!entityType,
    staleTime: 30_000,
  });
}

export function useDecisionEvidence(entityId: string, entityType: string) {
  return useQuery({
    queryKey: decisionKeys.evidence(entityId),
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/evidence", {
        params: { entity_id: entityId, entity_type: entityType },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data as EvidenceItem[];
    },
    enabled: !!entityId && !!entityType,
    staleTime: 30_000,
  });
}

export function useDecisionFeedback() {
  const queryClient = useQueryClient();
  return useMutation<Feedback, Error, DecisionFeedbackRequest>({
    mutationFn: async ({ decisionId, ...payload }) => {
      const response = await api.post(
        "/api/v1/decision/feedback",
        {
          decision_id: decisionId,
          ...payload,
        },
        {
          headers: { "X-Tenant-Id": getTenantId() },
        }
      );
      return response.data;
    },
    onSuccess: () => {
      const tenantId = getTenantId();
      queryClient.invalidateQueries({
        queryKey: decisionKeys.history(tenantId),
      });
      queryClient.invalidateQueries({
        queryKey: decisionKeys.feedback(tenantId),
      });
    },
  });
}

export function useDecisionFeedbackStats() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: decisionKeys.feedback(tenantId),
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/feedback/stats", {
        headers: { "X-Tenant-Id": tenantId },
      });
      return response.data as DecisionFeedbackStatsResponse;
    },
    staleTime: 30_000,
  });
}
