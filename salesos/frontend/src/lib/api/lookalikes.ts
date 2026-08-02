/**
 * GTM lookalike accounts HTTP (STORY-11-04 / FE-S11-04).
 * Tip in-memory won/lost Opportunity fixtures. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/lookalikes";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface LookalikeBody {
  name: string;
  company_name: string;
  industry?: string;
  city?: string;
  employees_count?: number | null;
  limit?: number;
  id?: string;
}

export interface LookalikeHit {
  company_id: string;
  company_name: string;
  industry: string;
  city: string;
  employees_count: number | null;
  similarity: number;
  outcome_affinity: string;
  matched_features: string[];
}

export interface LookalikeRun {
  id: string;
  tenant_id: string;
  name: string;
  seed: {
    company_name?: string;
    industry?: string;
    city?: string;
    employees_count?: number | null;
  };
  hits: LookalikeHit[];
  trained_on_won: number;
  trained_on_lost: number;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
  hit_count: number;
}

export interface LookalikeMeta {
  object: string;
  training: string;
  features: string[];
  honesty: string;
}

export async function getLookalikeMeta(
  tenantId: string,
): Promise<LookalikeMeta> {
  const resp = await api.get<LookalikeMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listLookalikeRuns(
  tenantId: string,
): Promise<LookalikeRun[]> {
  const resp = await api.get<LookalikeRun[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getLookalikeRun(
  tenantId: string,
  modelId: string,
): Promise<LookalikeRun> {
  const resp = await api.get<LookalikeRun>(`${BASE}/${modelId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function runLookalikes(
  tenantId: string,
  body: LookalikeBody,
): Promise<LookalikeRun> {
  const resp = await api.post<LookalikeRun>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
