"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getLeadDiscovery,
  getLeadDiscoveryMeta,
  listLeadDiscovery,
  runLeadDiscovery,
  type LeadDiscoveryBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useLeadDiscoveryMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.leadDiscoveryMeta(tenantId),
    queryFn: () => getLeadDiscoveryMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useLeadDiscoveryList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.leadDiscoveryList(tenantId),
    queryFn: () => listLeadDiscovery(tenantId),
    staleTime: 10_000,
  });
}

export function useLeadDiscoveryDetail(runId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.leadDiscoveryDetail(tenantId, runId ?? ""),
    queryFn: () => getLeadDiscovery(tenantId, runId as string),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
}

export function useRunLeadDiscovery() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: LeadDiscoveryBody) => runLeadDiscovery(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.leadDiscoveryList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.leadDiscoveryDetail(getTenantId(), row.id), row);
    },
  });
}
