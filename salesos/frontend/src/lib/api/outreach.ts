/**
 * GTM AI Outreach HTTP (STORY-11-08 / FE-S11-08).
 * Tip FixtureOutreachGenerator + governed prompt. draft_only — no live send.
 * feature_ai_copilot remains False. Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/outreach";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface OutreachBody {
  company_name: string;
  contact_name?: string;
  contact_title?: string;
  channel?: string;
  intent?: string;
  value_prop?: string;
  website_summary?: string;
  icp_notes?: string;
  generator_key?: string;
  id?: string;
}

export interface OutreachDraft {
  id: string;
  tenant_id: string;
  request: Record<string, unknown>;
  subject: string;
  body: string;
  channel: string;
  prompt_id: string;
  prompt_version: string;
  spend_path: string;
  generator_key: string;
  delivery_status: string;
  schema_version: number;
  created_at?: string;
  warnings: string[];
}

export interface OutreachMeta {
  object: string;
  capability: string;
  prompt_id: string;
  prompt_version: string;
  channels: string[];
  intents: string[];
  spend_path: string;
  generators_configured: string[];
  delivery_status: string;
  feature_ai_copilot: boolean;
  honesty: string;
}

export async function getOutreachMeta(tenantId: string): Promise<OutreachMeta> {
  const resp = await api.get<OutreachMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listOutreachDrafts(tenantId: string): Promise<OutreachDraft[]> {
  const resp = await api.get<OutreachDraft[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getOutreachDraft(tenantId: string, runId: string): Promise<OutreachDraft> {
  const resp = await api.get<OutreachDraft>(`${BASE}/${encodeURIComponent(runId)}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function createOutreachDraft(
  tenantId: string,
  body: OutreachBody
): Promise<OutreachDraft> {
  const resp = await api.post<OutreachDraft>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
