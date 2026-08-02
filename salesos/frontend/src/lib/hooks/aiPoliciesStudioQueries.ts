"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  deleteAiPolicy,
  evaluateAiPolicy,
  getAiPoliciesMeta,
  getAiPolicy,
  listAiPolicies,
  upsertAiPolicy,
  type AiPolicyEvaluateBody,
  type AiPolicyUpsertBody,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useAiPoliciesMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiPoliciesMeta(tenantId),
    queryFn: () => getAiPoliciesMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useAiPoliciesList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiPoliciesList(tenantId),
    queryFn: () => listAiPolicies(tenantId),
    staleTime: 10_000,
  });
}

export function useAiPolicyDetail(policyId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiPoliciesDetail(tenantId, policyId ?? ""),
    queryFn: () => getAiPolicy(tenantId, policyId as string),
    enabled: Boolean(policyId),
    staleTime: 10_000,
  });
}

function invalidateAll(qc: ReturnType<typeof useQueryClient>) {
  qc.invalidateQueries({ queryKey: tenantStudioKeys.all });
}

export function useUpsertAiPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: AiPolicyUpsertBody) =>
      upsertAiPolicy(getTenantId(), body),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useDeleteAiPolicy() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (policyId: string) =>
      deleteAiPolicy(getTenantId(), policyId),
    onSuccess: () => invalidateAll(qc),
  });
}

export function useEvaluateAiPolicy() {
  return useMutation({
    mutationFn: (body: AiPolicyEvaluateBody) =>
      evaluateAiPolicy(getTenantId(), body),
  });
}
