"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getWebsiteIntelligence,
  getWebsiteIntelligenceMeta,
  listWebsiteIntelligence,
  runWebsiteIntelligence,
  type WebsiteIntelligenceBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useWebsiteIntelligenceMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.websiteIntelMeta(tenantId),
    queryFn: () => getWebsiteIntelligenceMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useWebsiteIntelligenceList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.websiteIntelList(tenantId),
    queryFn: () => listWebsiteIntelligence(tenantId),
    staleTime: 10_000,
  });
}

export function useWebsiteIntelligenceDetail(runId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.websiteIntelDetail(tenantId, runId ?? ""),
    queryFn: () => getWebsiteIntelligence(tenantId, runId as string),
    enabled: Boolean(runId),
    staleTime: 10_000,
  });
}

export function useRunWebsiteIntelligence() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: WebsiteIntelligenceBody) =>
      runWebsiteIntelligence(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: gtmKeys.all });
    },
  });
}
