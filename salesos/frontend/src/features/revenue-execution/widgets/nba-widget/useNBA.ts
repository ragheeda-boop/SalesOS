import { useCallback } from "react";
import {
  useDecisionEvaluate,
  useDecisionFeedback,
} from "@/lib/decisionQueries";
import type {
  DecisionContext,
  DecisionResult,
} from "@salesos/platform/decision/contracts";

export type NBARecommendation = DecisionResult;

export function useNBA(opportunityId: string) {
  const evaluateMutation = useDecisionEvaluate();
  const feedbackMutation = useDecisionFeedback();

  const getNBA = useCallback(async (): Promise<NBARecommendation | null> => {
    try {
      const result = await evaluateMutation.mutateAsync({
        context: {
          tenantId: "",
          actorId: "",
          opportunityId,
          entityType: "opportunity",
        } as DecisionContext,
      });
      return result;
    } catch {
      return null;
    }
  }, [opportunityId, evaluateMutation]);

  const refreshNBA = useCallback(async (): Promise<NBARecommendation | null> => {
    try {
      const result = await evaluateMutation.mutateAsync({
        context: {
          tenantId: "",
          actorId: "",
          opportunityId,
          entityType: "opportunity",
        } as DecisionContext,
      });
      return result;
    } catch {
      return null;
    }
  }, [opportunityId, evaluateMutation]);

  const acceptNBA = useCallback(async (nbaId: string) => {
    await feedbackMutation.mutateAsync({
      decisionId: nbaId,
      outcome: "accepted",
    });
  }, [feedbackMutation]);

  const dismissNBA = useCallback(async (nbaId: string, reason?: string) => {
    await feedbackMutation.mutateAsync({
      decisionId: nbaId,
      outcome: "rejected",
      reason,
    });
  }, [feedbackMutation]);

  return { getNBA, refreshNBA, acceptNBA, dismissNBA };
}
