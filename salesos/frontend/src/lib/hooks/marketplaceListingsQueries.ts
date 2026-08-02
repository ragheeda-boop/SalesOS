"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  certifyMarketplaceListing,
  getMarketplaceCertifyMeta,
  getMarketplaceListing,
  getMarketplaceListingsMeta,
  installMarketplaceListing,
  listMarketplaceCatalogInstalls,
  listMarketplaceListings,
  publishMarketplaceListing,
  seedFirstPartyMarketplaceListings,
  seedMarketplacePublishPack,
  submitMarketplaceListing,
  type MarketplaceCertifyBody,
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

export function useMarketplaceCertifyMeta() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: marketplaceListingsKeys.certifyMeta(tenantId),
    queryFn: () => getMarketplaceCertifyMeta(tenantId),
    staleTime: 60_000,
  });
}

export function useMarketplaceCatalogInstalls() {
  const tenantId = getTenantId();
  return useQuery({
    queryKey: marketplaceListingsKeys.installs(tenantId),
    queryFn: () => listMarketplaceCatalogInstalls(tenantId),
    staleTime: 10_000,
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

export function useSeedMarketplacePublishPack() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => seedMarketplacePublishPack(getTenantId()),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}

export function usePublishMarketplaceListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (listingIdOrSlug: string) =>
      publishMarketplaceListing(getTenantId(), listingIdOrSlug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}

export function useInstallMarketplaceListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (listingIdOrSlug: string) =>
      installMarketplaceListing(getTenantId(), listingIdOrSlug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}

export function useSubmitMarketplaceListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (listingIdOrSlug: string) =>
      submitMarketplaceListing(getTenantId(), listingIdOrSlug),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}

export function useCertifyMarketplaceListing() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      listingIdOrSlug,
      body,
    }: {
      listingIdOrSlug: string;
      body?: MarketplaceCertifyBody;
    }) => certifyMarketplaceListing(getTenantId(), listingIdOrSlug, body),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: marketplaceListingsKeys.all });
    },
  });
}
