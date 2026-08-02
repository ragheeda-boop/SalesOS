"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getEnrichmentMeta,
  getEnrichmentRun,
  listEnrichmentRuns,
  runEnrichment,
  type EnrichmentBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useEnrichmentMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.enrichmentMeta(tenantId),
    queryFn: () => getEnrichmentMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useEnrichmentList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.enrichmentList(tenantId),
    queryFn: () => listEnrichmentRuns(tenantId),
    staleTime: 10_000,
  });
}

export function useEnrichmentDetail(runId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.enrichmentDetail(tenantId, runId ?? ""),
    queryFn: () => getEnrichmentRun(tenantId, runId as string),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
}

export function useRunEnrichment() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: EnrichmentBody) => runEnrichment(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.enrichmentList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.enrichmentDetail(getTenantId(), row.id), row);
    },
  });
}
