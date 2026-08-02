/**
 * GTM enrichment waterfall HTTP (STORY-11-05 / FE-S11-05).
 * Tip ≥2 FakeEnrichment providers. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/enrichment";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface EnrichmentBody {
  company_name: string;
  domain?: string;
  external_id?: string;
  known?: Record<string, unknown>;
  provider_order?: string[];
  id?: string;
}

export interface EnrichmentHit {
  field: string;
  value: unknown;
  provider_key: string;
}

export interface EnrichmentRun {
  id: string;
  tenant_id: string;
  request: {
    company_name: string;
    domain: string;
    external_id: string;
    known: Record<string, unknown>;
    provider_order: string[];
  };
  filled: Record<string, unknown>;
  hits: EnrichmentHit[];
  providers_attempted: string[];
  providers_configured: string[];
  missing_fields: string[];
  schema_version: number;
  created_at?: string;
  complete: boolean;
}

export interface EnrichmentMeta {
  enrichable_fields: string[];
  providers_configured: string[];
  policy: string;
  honesty: string;
}

export async function getEnrichmentMeta(
  tenantId: string,
): Promise<EnrichmentMeta> {
  const resp = await api.get<EnrichmentMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listEnrichmentRuns(
  tenantId: string,
): Promise<EnrichmentRun[]> {
  const resp = await api.get<EnrichmentRun[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getEnrichmentRun(
  tenantId: string,
  runId: string,
): Promise<EnrichmentRun> {
  const resp = await api.get<EnrichmentRun>(`${BASE}/${runId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function runEnrichment(
  tenantId: string,
  body: EnrichmentBody,
): Promise<EnrichmentRun> {
  const resp = await api.post<EnrichmentRun>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
