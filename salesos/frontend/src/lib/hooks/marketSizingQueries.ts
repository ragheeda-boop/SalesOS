"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  computeMarketSizing,
  getMarketSizing,
  getMarketSizingMeta,
  listMarketSizing,
  type MarketSizingComputeBody,
} from "@/lib/api";
import { gtmKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useMarketSizingMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.marketSizingMeta(tenantId),
    queryFn: () => getMarketSizingMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useMarketSizingList() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.marketSizingList(tenantId),
    queryFn: () => listMarketSizing(tenantId),
    staleTime: 10_000,
  });
}

export function useMarketSizingDetail(snapshotId: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: gtmKeys.marketSizingDetail(tenantId, snapshotId ?? ""),
    queryFn: () => getMarketSizing(tenantId, snapshotId as string),
    enabled: Boolean(snapshotId),
    staleTime: 10_000,
  });
}

export function useComputeMarketSizing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: MarketSizingComputeBody) => computeMarketSizing(getTenantId(), body),
    onSuccess: (row) => {
      qc.invalidateQueries({
        queryKey: gtmKeys.marketSizingList(getTenantId()),
      });
      qc.setQueryData(gtmKeys.marketSizingDetail(getTenantId(), row.id), row);
    },
  });
}
