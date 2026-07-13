"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";
import { decisionKeys } from "@/lib/queryKeys";
import { getTenantId } from "./hooks/useTenant";
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
      const response = await api.post("/api/v1/decision/evaluate", { context }, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
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

export function useDecisionRecommendations(entityId?: string, entityType?: string) {
  return useQuery({
    queryKey: [...decisionKeys.recommendations(entityId), { entityType }],
    queryFn: async () => {
      const response = await api.get("/api/v1/decision/recommendations", {
        params: { entity_id: entityId, entity_type: entityType },
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data as Recommendation[];
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
      return response.data as Score[];
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
      const response = await api.post("/api/v1/decision/feedback", {
        decision_id: decisionId,
        ...payload,
      }, {
        headers: { "X-Tenant-Id": getTenantId() },
      });
      return response.data;
    },
    onSuccess: () => {
      const tenantId = getTenantId();
      queryClient.invalidateQueries({ queryKey: decisionKeys.history(tenantId) });
      queryClient.invalidateQueries({ queryKey: decisionKeys.feedback(tenantId) });
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
