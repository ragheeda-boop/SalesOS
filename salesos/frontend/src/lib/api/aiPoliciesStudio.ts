/**
 * Studio AI Policies HTTP (STORY-12-02 / FE-S12-02).
 * Tip in-memory CAP-091; reuses AI-GR-* primitives.
 * feature_ai_copilot remains False. No live LLM / RAG GO. Not Production GO.
 */
import api from "./client";

const BASE = "/api/v1/studio/ai-policies";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface DataClassRule {
  data_class: string;
  max_model_tier: string;
  require_pii_scrub: boolean;
}

export interface AiPolicySet {
  id: string;
  tenant_id: string;
  name: string;
  guardrails: Record<string, boolean>;
  data_class_rules: DataClassRule[];
  schema_version: number;
  created_at?: string;
  updated_at?: string;
}

export interface AiPoliciesMeta {
  object: string;
  capability: string;
  reuses: string[];
  guardrail_catalog: Record<string, string>;
  data_classes: string[];
  model_tiers: string[];
  feature_ai_copilot: boolean;
  honesty: string;
}

export interface AiPolicyUpsertBody {
  id?: string | null;
  name: string;
  guardrails?: Record<string, boolean>;
  data_class_rules?: DataClassRule[];
}

export interface AiPolicyEvaluateBody {
  data_class: string;
  requested_model_tier?: string;
  sample_text?: string;
  policy_id?: string | null;
}

export interface AiPolicyEvaluateResult {
  allowed: boolean;
  data_class: string;
  requested_model_tier: string;
  max_model_tier: string;
  require_pii_scrub: boolean;
  sanitized_preview: string;
  redactions: Record<string, number>;
  findings: string[];
  live_llm: boolean;
  feature_ai_copilot: boolean;
}

export async function getAiPoliciesMeta(tenantId: string): Promise<AiPoliciesMeta> {
  const resp = await api.get<AiPoliciesMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listAiPolicies(tenantId: string): Promise<AiPolicySet[]> {
  const resp = await api.get<AiPolicySet[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getAiPolicy(tenantId: string, policyId: string): Promise<AiPolicySet> {
  const resp = await api.get<AiPolicySet>(`${BASE}/${policyId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertAiPolicy(
  tenantId: string,
  body: AiPolicyUpsertBody
): Promise<AiPolicySet> {
  const resp = await api.post<AiPolicySet>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function deleteAiPolicy(
  tenantId: string,
  policyId: string
): Promise<{ deleted: boolean; id: string }> {
  const resp = await api.delete<{ deleted: boolean; id: string }>(`${BASE}/${policyId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function evaluateAiPolicy(
  tenantId: string,
  body: AiPolicyEvaluateBody
): Promise<AiPolicyEvaluateResult> {
  const resp = await api.post<AiPolicyEvaluateResult>(`${BASE}/evaluate`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
