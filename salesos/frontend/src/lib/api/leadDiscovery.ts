/**
 * GTM lead discovery HTTP (STORY-11-03 / FE-S11-03).
 * Tip gov-first + FakeSourceConnector fallback. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/lead-discovery";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface LeadDiscoveryQuery {
  industries: string[];
  cities: string[];
  employees_min: number | null;
  employees_max: number | null;
  limit: number;
}

export interface LeadDiscoveryBody {
  name: string;
  industries?: string[];
  cities?: string[];
  employees_min?: number | null;
  employees_max?: number | null;
  limit?: number;
  id?: string;
  use_provider_fallback?: boolean;
}

export interface DiscoveredLead {
  id: string;
  company_name: string;
  industry: string;
  city: string;
  employees_count: number | null;
  source: string;
  external_id: string;
}

export interface LeadDiscoveryRun {
  id: string;
  tenant_id: string;
  name: string;
  query: LeadDiscoveryQuery;
  leads: DiscoveredLead[];
  government_hit_count: number;
  provider_hit_count: number;
  provider_key: string;
  dataset_scale_hint: number;
  schema_version: number;
  created_at?: string;
  government_first_ok: boolean;
  total_hits: number;
}

export interface LeadDiscoveryMeta {
  dataset_scale_hint: number;
  filters: string[];
  sourcing_order: string[];
  honesty: string;
}

export async function getLeadDiscoveryMeta(tenantId: string): Promise<LeadDiscoveryMeta> {
  const resp = await api.get<LeadDiscoveryMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listLeadDiscovery(tenantId: string): Promise<LeadDiscoveryRun[]> {
  const resp = await api.get<LeadDiscoveryRun[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getLeadDiscovery(tenantId: string, runId: string): Promise<LeadDiscoveryRun> {
  const resp = await api.get<LeadDiscoveryRun>(`${BASE}/${runId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function runLeadDiscovery(
  tenantId: string,
  body: LeadDiscoveryBody
): Promise<LeadDiscoveryRun> {
  const resp = await api.post<LeadDiscoveryRun>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
