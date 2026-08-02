"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getMarketplaceListing,
  getMarketplaceListingsMeta,
  listMarketplaceListings,
  seedFirstPartyMarketplaceListings,
} from "@/lib/api";
import { marketplaceListingsKeys } from "@/lib/queryKeys";
import { getTenantId } from "./useTenant";

export function useMarketplaceListingsMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: marketplaceListingsKeys.meta(tenantId),
    queryFn: () => getMarketplaceListingsMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useMarketplaceListings(filters: {
  listing_type?: string;
  status?: string;
}) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: marketplaceListingsKeys.list(
      tenantId,
      filters.listing_type || "",
      filters.status || "",
    ),
    queryFn: () => listMarketplaceListings(tenantId, filters),
    staleTime: 10_000,
  });
}

export function useMarketplaceListing(idOrSlug: string | null) {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: marketplaceListingsKeys.detail(tenantId, idOrSlug || ""),
    queryFn: () => getMarketplaceListing(tenantId, idOrSlug!),
    enabled: Boolean(idOrSlug),
    staleTime: 10_000,
  });
}

export function useSeedFirstPartyMarketplaceListings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => seedFirstPartyMarketplaceListings(getTenantId()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}
