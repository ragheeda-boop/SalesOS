/**
 * Tenant Studio territories HTTP (STORY-10-05 / FE-S10-05).
 * Tip in-memory config over CAP-017 runtime. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/studio/territories";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface TerritoryMatchCondition {
  field: string;
  op: string;
  value?: unknown;
}

export interface TerritoryRule {
  id: string;
  tenant_id: string;
  name: string;
  territory_key: string;
  region: string;
  rep_id: string;
  priority: number;
  match_conditions: TerritoryMatchCondition[];
  active: boolean;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

export interface TerritoryRuleUpsert {
  id?: string;
  name: string;
  territory_key: string;
  region?: string;
  rep_id?: string;
  priority?: number;
  match_conditions: TerritoryMatchCondition[];
  active?: boolean;
}

export interface TerritoriesMeta {
  match_fields: string[];
  match_ops: string[];
  dimensions: string[];
  persistence: string;
  runtime: string;
  policy_count_delta: number;
}

export interface TerritoryAssignBody {
  attributes: Record<string, unknown>;
  rule_id?: string | null;
}

export interface TerritoryAssignResult {
  matched: boolean;
  territory_key: string | null;
  rule_id: string | null;
  region: string;
  rep_id: string;
  source: string;
  explanation: string[];
}

export async function getTerritoriesMeta(tenantId: string): Promise<TerritoriesMeta> {
  const resp = await api.get<TerritoriesMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listTerritoryRules(tenantId: string): Promise<TerritoryRule[]> {
  const resp = await api.get<TerritoryRule[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getTerritoryRule(tenantId: string, ruleId: string): Promise<TerritoryRule> {
  const resp = await api.get<TerritoryRule>(`${BASE}/${ruleId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertTerritoryRule(
  tenantId: string,
  body: TerritoryRuleUpsert
): Promise<TerritoryRule> {
  const resp = await api.post<TerritoryRule>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function deleteTerritoryRule(
  tenantId: string,
  ruleId: string
): Promise<{ deleted: boolean; id: string }> {
  const resp = await api.delete<{ deleted: boolean; id: string }>(`${BASE}/${ruleId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function assignTerritory(
  tenantId: string,
  body: TerritoryAssignBody
): Promise<TerritoryAssignResult> {
  const resp = await api.post<TerritoryAssignResult>(`${BASE}/assign`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
