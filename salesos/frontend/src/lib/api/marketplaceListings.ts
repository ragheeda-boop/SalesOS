/**
 * Marketplace listings HTTP (STORY-13-01/02/04 / FE-S13-04).
 * Tip memory catalog + CAP-094 certify + publish pack / catalog install.
 * Catalog install ≠ live ERP. Not CAP-036 stub. Not Production GO.
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
  installable?: boolean;
}

export interface MarketplaceListingsMeta {
  listing_types: string[];
  statuses: string[];
  object: string;
  obj_id: string;
  persistence: string;
  policy_count_delta: number;
  honesty: string;
  certify_stages?: string[];
  publish_pack?: {
    story: string;
    min_connectors: number;
    min_playbooks: number;
    seed_slugs: string[];
    connector_keys: string[];
  };
}

export interface MarketplaceCatalogInstall {
  id: string;
  tenant_id: string;
  listing_id: string;
  listing_slug: string;
  listing_type: string;
  connector_key: string;
  installed_at: string;
  honesty: string;
}

export interface MarketplaceCertifyMeta {
  capability: string;
  stages: string[];
  conformance_suite: string;
  via: string;
  trial_sandbox: string;
  not_domains_marketplace_sandbox: boolean;
  first_party_checklist_exception: boolean;
  feature_ai_copilot: boolean;
  honesty: string;
}

export interface MarketplaceCertifyStage {
  stage: string;
  ok: boolean;
  detail: Record<string, unknown>;
}

export interface MarketplaceCertifyReport {
  listing_id: string;
  ok: boolean;
  status_before: string;
  status_after: string;
  stages: MarketplaceCertifyStage[];
  ran_at: string;
  honesty: string;
}

export interface MarketplaceCertifyBody {
  real_tenant_ids?: string[];
  auto_submit?: boolean;
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

export async function seedMarketplacePublishPack(
  tenantId: string,
): Promise<MarketplaceListing[]> {
  const resp = await api.post<MarketplaceListing[]>(
    `${BASE}/seed-publish-pack`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function listMarketplaceCatalogInstalls(
  tenantId: string,
): Promise<MarketplaceCatalogInstall[]> {
  const resp = await api.get<MarketplaceCatalogInstall[]>(`${BASE}/installs`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function publishMarketplaceListing(
  tenantId: string,
  listingIdOrSlug: string,
): Promise<MarketplaceListing> {
  const resp = await api.post<MarketplaceListing>(
    `${BASE}/${encodeURIComponent(listingIdOrSlug)}/publish`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function installMarketplaceListing(
  tenantId: string,
  listingIdOrSlug: string,
): Promise<MarketplaceCatalogInstall> {
  const resp = await api.post<MarketplaceCatalogInstall>(
    `${BASE}/${encodeURIComponent(listingIdOrSlug)}/install`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function getMarketplaceCertifyMeta(
  tenantId: string,
): Promise<MarketplaceCertifyMeta> {
  const resp = await api.get<MarketplaceCertifyMeta>(`${BASE}/certify/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function submitMarketplaceListing(
  tenantId: string,
  listingIdOrSlug: string,
): Promise<MarketplaceListing> {
  const resp = await api.post<MarketplaceListing>(
    `${BASE}/${encodeURIComponent(listingIdOrSlug)}/submit`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function certifyMarketplaceListing(
  tenantId: string,
  listingIdOrSlug: string,
  body?: MarketplaceCertifyBody,
): Promise<MarketplaceCertifyReport> {
  const resp = await api.post<MarketplaceCertifyReport>(
    `${BASE}/${encodeURIComponent(listingIdOrSlug)}/certify`,
    {
      real_tenant_ids: body?.real_tenant_ids ?? [],
      auto_submit: body?.auto_submit ?? true,
    },
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
