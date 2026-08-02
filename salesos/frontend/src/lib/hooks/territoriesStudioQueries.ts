"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  assignTerritory,
  deleteTerritoryRule,
  getTerritoriesMeta,
  listTerritoryRules,
  upsertTerritoryRule,
  type TerritoryAssignBody,
  type TerritoryRuleUpsert,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useTerritoriesMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.territoriesMeta(tenantId),
    queryFn: () => getTerritoriesMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useTerritoryRules() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.territories(tenantId),
    queryFn: () => listTerritoryRules(tenantId),
    staleTime: 10_000,
  });
}

export function useUpsertTerritoryRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: TerritoryRuleUpsert) =>
      upsertTerritoryRule(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.territories(getTenantId()),
      });
    },
  });
}

export function useDeleteTerritoryRule() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (ruleId: string) => deleteTerritoryRule(getTenantId(), ruleId),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.territories(getTenantId()),
      });
    },
  });
}

export function useAssignTerritory() {
  return useMutation({
    mutationFn: (body: TerritoryAssignBody) =>
      assignTerritory(getTenantId(), body),
  });
}
