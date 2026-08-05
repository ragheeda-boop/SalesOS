"use client";

/**
 * DecisionProvider — prefers Decision Platform HTTP API (not the FE package stub).
 * Local ScoringEngine remains for client-side score helpers only.
 * Do not market as production AI GA. See AI_HONESTY.md / PROD-W6-001.
 */

import { createContext, useContext, useCallback, useMemo } from "react";
import { ScoringEngine } from "@salesos/decision-platform";
import type {
  DecisionContext,
  DecisionResult,
  DecisionHistoryItem,
  Explainability,
  Feedback,
  Score,
  ScoreType,
} from "@salesos/decision-platform";
import api from "@/lib/api";
import { getTenantId } from "@/lib/hooks/useTenant";

interface DecisionContextValue {
  evaluate: (context: DecisionContext) => Promise<DecisionResult>;
  evaluateBatch: (contexts: DecisionContext[]) => Promise<DecisionResult[]>;
  getRecommendation: (
    opportunityId: string,
    tenantId: string,
    actorId: string
  ) => Promise<DecisionResult>;
  getScores: (
    entityId: string,
    entityType: DecisionContext["entityType"],
    tenantId: string,
    actorId: string
  ) => Promise<Score[]>;
  getHistory: (tenantId: string, limit?: number) => Promise<DecisionHistoryItem[]>;
  getExplainability: (decisionId: string) => Promise<Explainability | null>;
  submitFeedback: (feedback: Feedback) => Promise<{ id: string; accepted: boolean }>;
  getFeedbackStats: (tenantId: string) => Promise<FeedbackStats>;
  score: (
    type: ScoreType,
    factors: Record<string, number>,
    metadata?: Record<string, unknown>
  ) => Score;
}

interface FeedbackStats {
  total: number;
  accepted: number;
  rejected: number;
  ignored: number;
  acceptanceRate: number;
  totalRevenueImpact: number;
  averageTimeToExecution: number | null;
}

const DecisionCtx = createContext<DecisionContextValue | null>(null);

const scoringEngine = new ScoringEngine();

function toApiContext(context: DecisionContext) {
  const tenantId = context.tenantId || getTenantId();
  return {
    tenant_id: tenantId,
    actor_id: context.actorId,
    entity_id: context.entityId,
    entity_type: context.entityType,
    opportunity_id: context.opportunityId,
    company_id: context.companyId,
    signal_id: context.signalId,
    metadata: context.metadata,
  };
}

function tenantHeaders(tenantId?: string) {
  return { "X-Tenant-Id": tenantId || getTenantId() };
}

export function DecisionProvider({ children }: { children: React.ReactNode }) {
  const evaluate = useCallback(async (context: DecisionContext) => {
    const body = toApiContext(context);
    const response = await api.post("/api/v1/decision/evaluate", body, {
      headers: tenantHeaders(body.tenant_id),
    });
    return response.data as DecisionResult;
  }, []);

  const evaluateBatch = useCallback(async (contexts: DecisionContext[]) => {
    const bodies = contexts.map(toApiContext);
    const tenantId = bodies[0]?.tenant_id || getTenantId();
    const response = await api.post("/api/v1/decision/batch", bodies, {
      headers: tenantHeaders(tenantId),
    });
    const data = response.data;
    if (Array.isArray(data)) return data as DecisionResult[];
    return (data?.results ?? []) as DecisionResult[];
  }, []);

  const getRecommendation = useCallback(
    async (opportunityId: string, tenantId: string, actorId: string) => {
      return evaluate({
        tenantId,
        actorId,
        opportunityId,
        entityType: "opportunity",
      });
    },
    [evaluate]
  );

  const getScores = useCallback(
    async (
      entityId: string,
      entityType: DecisionContext["entityType"],
      tenantId: string,
      actorId: string
    ) => {
      const result = await evaluate({
        tenantId,
        actorId,
        entityId,
        entityType,
      });
      return result.scores;
    },
    [evaluate]
  );

  const getHistory = useCallback(async (tenantId: string, limit?: number) => {
    const response = await api.get("/api/v1/decision/history", {
      params: { limit },
      headers: tenantHeaders(tenantId),
    });
    const data = response.data;
    return (data?.items ?? data ?? []) as DecisionHistoryItem[];
  }, []);

  const getExplainability = useCallback(async (decisionId: string) => {
    const response = await api.get(`/api/v1/decision/${decisionId}/explain`, {
      headers: tenantHeaders(),
    });
    const data = response.data;
    return (data?.explainability ?? data ?? null) as Explainability | null;
  }, []);

  const submitFeedback = useCallback(async (feedback: Feedback) => {
    const response = await api.post(
      "/api/v1/decision/feedback",
      {
        decision_id: feedback.decisionId,
        tenant_id: feedback.tenantId || getTenantId(),
        actor_id: "ui",
        outcome: feedback.outcome,
        revenue_impact: feedback.revenueImpact,
        timestamp: feedback.createdAt || new Date().toISOString(),
      },
      {
        headers: tenantHeaders(feedback.tenantId),
      }
    );
    const data = response.data;
    return {
      id: data?.id ?? feedback.id,
      accepted: data?.accepted ?? feedback.outcome === "accepted",
    };
  }, []);

  const getFeedbackStats = useCallback(async (tenantId: string) => {
    const response = await api.get("/api/v1/decision/feedback/stats", {
      headers: tenantHeaders(tenantId),
    });
    const data = response.data;
    return {
      total: data?.total ?? data?.totalFeedback ?? 0,
      accepted: data?.accepted ?? 0,
      rejected: data?.rejected ?? 0,
      ignored: data?.ignored ?? 0,
      acceptanceRate: data?.acceptanceRate ?? 0,
      totalRevenueImpact: data?.totalRevenueImpact ?? data?.avgRevenueImpact ?? 0,
      averageTimeToExecution: data?.averageTimeToExecution ?? null,
    } as FeedbackStats;
  }, []);

  const score = useCallback(
    (type: ScoreType, factors: Record<string, number>, metadata?: Record<string, unknown>) => {
      return scoringEngine.score(type, factors, metadata);
    },
    []
  );

  const value = useMemo<DecisionContextValue>(
    () => ({
      evaluate,
      evaluateBatch,
      getRecommendation,
      getScores,
      getHistory,
      getExplainability,
      submitFeedback,
      getFeedbackStats,
      score,
    }),
    [
      evaluate,
      evaluateBatch,
      getRecommendation,
      getScores,
      getHistory,
      getExplainability,
      submitFeedback,
      getFeedbackStats,
      score,
    ]
  );

  return <DecisionCtx.Provider value={value}>{children}</DecisionCtx.Provider>;
}

export function useDecision(): DecisionContextValue {
  const ctx = useContext(DecisionCtx);
  if (!ctx) {
    throw new Error("useDecision must be used within a DecisionProvider");
  }
  return ctx;
}

export function useDecisionSafe(): DecisionContextValue | null {
  try {
    return useDecision();
  } catch {
    return null;
  }
}

import type { DecisionContextData } from "@salesos/widget-sdk";

export function useCompanyDecision(_tenantId: string): DecisionContextData | null {
  const ctx = useContext(DecisionCtx);
  if (!ctx) {
    return null;
  }
  return null;
}
