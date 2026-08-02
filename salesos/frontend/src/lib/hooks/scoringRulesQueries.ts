"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  evaluateScoringRule,
  listScoringRules,
  upsertScoringRule,
  type ScoringEvaluateRequest,
  type ScoringRuleUpsert,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useScoringRules() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.scoringRules(tenantId),
    queryFn: () => listScoringRules(tenantId),
    staleTime: 10_000,
  });
}

export function useUpsertScoringRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: ScoringRuleUpsert) =>
      upsertScoringRule(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.scoringRules(getTenantId()),
      });
    },
  });
}

export function useEvaluateScoringRule() {
  return useMutation({
    mutationFn: (body: ScoringEvaluateRequest) =>
      evaluateScoringRule(getTenantId(), body),
  });
}
