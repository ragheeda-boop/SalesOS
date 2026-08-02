/**
 * GTM ICP profiles HTTP (STORY-11-01 / FE-S11-01).
 * Tip in-memory versioned ICPProfile + deterministic score. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/icp-profiles";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface ICPWeights {
  industry: number;
  city: number;
  employees: number;
  titles: number;
  keywords: number;
}

export interface ICPCriteria {
  industries: string[];
  cities: string[];
  employees_min: number | null;
  employees_max: number | null;
  titles: string[];
  keywords: string[];
}

export interface ICPProfileCreateBody {
  name: string;
  description?: string;
  industries?: string[];
  cities?: string[];
  employees_min?: number | null;
  employees_max?: number | null;
  titles?: string[];
  keywords?: string[];
  weights?: Partial<ICPWeights>;
  id?: string;
  is_active?: boolean;
}

export interface ICPProfileUpdateBody {
  name?: string;
  description?: string;
  industries?: string[];
  cities?: string[];
  employees_min?: number | null;
  employees_max?: number | null;
  titles?: string[];
  keywords?: string[];
  weights?: Partial<ICPWeights>;
  is_active?: boolean;
}

export interface ICPScoreBody {
  industry?: string;
  city?: string;
  employees_count?: number | null;
  title?: string;
  name?: string;
  description?: string;
  keywords?: string;
  notes?: string;
}

export interface ICPProfile {
  id: string;
  tenant_id: string;
  name: string;
  description: string;
  criteria: ICPCriteria;
  weights: ICPWeights;
  schema_version: number;
  is_active: boolean;
  created_at?: string;
  updated_at?: string;
}

export interface ICPScoreResult {
  profile_id: string;
  schema_version: number;
  score: number;
  max_score: number;
  fit_ratio: number;
  matched: Record<string, boolean>;
  company: Record<string, unknown>;
}

export interface ICPMeta {
  object: string;
  filters: string[];
  versioning: string;
  scoring: string;
  honesty: string;
}

export async function getIcpMeta(tenantId: string): Promise<ICPMeta> {
  const resp = await api.get<ICPMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listIcpProfiles(tenantId: string): Promise<ICPProfile[]> {
  const resp = await api.get<ICPProfile[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getIcpProfile(
  tenantId: string,
  profileId: string,
): Promise<ICPProfile> {
  const resp = await api.get<ICPProfile>(`${BASE}/${profileId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function createIcpProfile(
  tenantId: string,
  body: ICPProfileCreateBody,
): Promise<ICPProfile> {
  const resp = await api.post<ICPProfile>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function updateIcpProfile(
  tenantId: string,
  profileId: string,
  body: ICPProfileUpdateBody,
): Promise<ICPProfile> {
  const resp = await api.put<ICPProfile>(`${BASE}/${profileId}`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function scoreIcpProfile(
  tenantId: string,
  profileId: string,
  body: ICPScoreBody,
): Promise<ICPScoreResult> {
  const resp = await api.post<ICPScoreResult>(
    `${BASE}/${profileId}/score`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
