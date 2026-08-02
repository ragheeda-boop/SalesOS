"use client";

import { useQuery } from "@tanstack/react-query";
import {
  getAiModelTierCatalog,
  getAiModelTierDefaults,
  resolveAiModelTiers,
} from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useAiModelTierCatalog() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiModelTiersCatalog(tenantId),
    queryFn: () => getAiModelTierCatalog(tenantId),
    staleTime: 60_000,
  });
}

export function useAiModelTierDefaults(planTier: string) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiModelTiersDefaults(tenantId, planTier),
    queryFn: () => getAiModelTierDefaults(tenantId, planTier),
    staleTime: 30_000,
  });
}

export function useAiModelTiersResolve(requestedTier: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.aiModelTiersResolve(
      tenantId,
      requestedTier || "",
    ),
    queryFn: () => resolveAiModelTiers(tenantId, requestedTier),
    staleTime: 15_000,
  });
}
