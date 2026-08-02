/**
 * GTM market sizing HTTP (STORY-11-02 / FE-S11-02).
 * Tip in-memory gov-dataset-shaped universe. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/market-sizing";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface MarketSizingCriteria {
  industries: string[];
  cities: string[];
  employees_min: number | null;
  employees_max: number | null;
}

export interface MarketSizingComputeBody {
  name: string;
  industries?: string[];
  cities?: string[];
  employees_min?: number | null;
  employees_max?: number | null;
  id?: string;
}

export interface MarketSizingSnapshot {
  id: string;
  tenant_id: string;
  name: string;
  criteria: MarketSizingCriteria;
  tam: number;
  sam: number;
  som: number;
  universe_size: number;
  dataset_scale_hint: number;
  schema_version: number;
  created_at?: string;
  invariant_ok: boolean;
}

export interface MarketSizingMeta {
  dataset_scale_hint: number;
  filters: string[];
  invariant: string;
  honesty: string;
}

export async function getMarketSizingMeta(
  tenantId: string,
): Promise<MarketSizingMeta> {
  const resp = await api.get<MarketSizingMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listMarketSizing(
  tenantId: string,
): Promise<MarketSizingSnapshot[]> {
  const resp = await api.get<MarketSizingSnapshot[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getMarketSizing(
  tenantId: string,
  snapshotId: string,
): Promise<MarketSizingSnapshot> {
  const resp = await api.get<MarketSizingSnapshot>(`${BASE}/${snapshotId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function computeMarketSizing(
  tenantId: string,
  body: MarketSizingComputeBody,
): Promise<MarketSizingSnapshot> {
  const resp = await api.post<MarketSizingSnapshot>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
