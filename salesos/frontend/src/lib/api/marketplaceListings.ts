/**
 * Marketplace listings HTTP (STORY-13-01 / FE browse).
 * Tip in-memory Owner catalog. Not CAP-036 plugin stub. Not Production GO.
 */
import api from "./client";

const BASE = "/api/v1/marketplace/listings";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface MarketplaceListing {
  id: string;
  slug: string;
  name: string;
  listing_type: string;
  version: string;
  status: string;
  description: string;
  publisher: string;
  first_party: boolean;
  connector_key: string;
  tags: string[];
  manifest: Record<string, unknown>;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

export interface MarketplaceListingsMeta {
  listing_types: string[];
  statuses: string[];
  object: string;
  obj_id: string;
  persistence: string;
  policy_count_delta: number;
  honesty: string;
}

export async function getMarketplaceListingsMeta(
  tenantId: string,
): Promise<MarketplaceListingsMeta> {
  const resp = await api.get<MarketplaceListingsMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listMarketplaceListings(
  tenantId: string,
  params?: { listing_type?: string; status?: string },
): Promise<MarketplaceListing[]> {
  const resp = await api.get<MarketplaceListing[]>(BASE, {
    headers: tenantHeaders(tenantId),
    params: {
      ...(params?.listing_type ? { listing_type: params.listing_type } : {}),
      ...(params?.status ? { status: params.status } : {}),
    },
  });
  return resp.data;
}

export async function getMarketplaceListing(
  tenantId: string,
  listingIdOrSlug: string,
): Promise<MarketplaceListing> {
  const resp = await api.get<MarketplaceListing>(
    `${BASE}/${encodeURIComponent(listingIdOrSlug)}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function seedFirstPartyMarketplaceListings(
  tenantId: string,
): Promise<MarketplaceListing[]> {
  const resp = await api.post<MarketplaceListing[]>(
    `${BASE}/seed-first-party`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
