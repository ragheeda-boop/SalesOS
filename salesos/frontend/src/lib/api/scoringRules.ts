/**
 * Tenant Studio scoring-rules HTTP (STORY-10-04 / FE-S10-04).
 * Tip in-memory store — no Postgres claim. Deterministic rules only (not LLM).
 * Not Production GO / RAG GO.
 */
import api from "./client";
import type {
  ScoringEvaluateRequest,
  ScoringEvaluateResponse,
  ScoringRule,
  ScoringRuleUpsert,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/scoring-rules";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listScoringRules(
  tenantId: string,
): Promise<ScoringRule[]> {
  const resp = await api.get<ScoringRule[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertScoringRule(
  tenantId: string,
  body: ScoringRuleUpsert,
): Promise<ScoringRule> {
  const resp = await api.post<ScoringRule>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getScoringRule(
  tenantId: string,
  ruleId: string,
): Promise<ScoringRule> {
  const resp = await api.get<ScoringRule>(`${BASE}/${ruleId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function evaluateScoringRule(
  tenantId: string,
  body: ScoringEvaluateRequest,
): Promise<ScoringEvaluateResponse> {
  const resp = await api.post<ScoringEvaluateResponse>(
    `${BASE}/evaluate`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
