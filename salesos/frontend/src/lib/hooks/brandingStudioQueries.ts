"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getBranding, upsertBranding, type BrandingUpsert } from "@/lib/api";
import { tenantStudioKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useBranding() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: tenantStudioKeys.branding(tenantId),
    queryFn: () => getBranding(tenantId),
    staleTime: 10_000,
  });
}

export function useUpsertBranding() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: BrandingUpsert) => upsertBranding(getTenantId(), body),
    onSuccess: () => {
      qc.invalidateQueries({
        queryKey: tenantStudioKeys.branding(getTenantId()),
      });
    },
  });
}
