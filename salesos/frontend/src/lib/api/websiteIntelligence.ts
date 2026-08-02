/**
 * GTM Website Intelligence HTTP (STORY-11-07 / FE-S11-07).
 * Tip FixtureWebsiteAnalyzer + governed prompt. No live crawl/LLM invent.
 * feature_ai_copilot remains False. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/website-intelligence";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface WebsiteIntelligenceBody {
  url: string;
  company_name?: string;
  page_snippet?: string;
  analyzer_key?: string;
  id?: string;
}

export interface WebsiteSignal {
  key: string;
  value: string;
  confidence: number;
}

export interface WebsiteIntelligenceSnapshot {
  id: string;
  tenant_id: string;
  request: {
    url?: string;
    company_name?: string;
    page_snippet?: string;
    [key: string]: unknown;
  };
  summary: string;
  signals: WebsiteSignal[];
  prompt_id: string;
  prompt_version: string;
  spend_path: string;
  analyzer_key: string;
  schema_version: number;
  created_at?: string;
  signal_count: number;
}

export interface WebsiteIntelligenceMeta {
  object: string;
  capability: string;
  prompt_id: string;
  prompt_version: string;
  spend_path: string;
  analyzers_configured: string[];
  feature_ai_copilot: boolean;
  honesty: string;
}

export async function getWebsiteIntelligenceMeta(
  tenantId: string,
): Promise<WebsiteIntelligenceMeta> {
  const resp = await api.get<WebsiteIntelligenceMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listWebsiteIntelligence(
  tenantId: string,
): Promise<WebsiteIntelligenceSnapshot[]> {
  const resp = await api.get<WebsiteIntelligenceSnapshot[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getWebsiteIntelligence(
  tenantId: string,
  runId: string,
): Promise<WebsiteIntelligenceSnapshot> {
  const resp = await api.get<WebsiteIntelligenceSnapshot>(
    `${BASE}/${encodeURIComponent(runId)}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function runWebsiteIntelligence(
  tenantId: string,
  body: WebsiteIntelligenceBody,
): Promise<WebsiteIntelligenceSnapshot> {
  const resp = await api.post<WebsiteIntelligenceSnapshot>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
