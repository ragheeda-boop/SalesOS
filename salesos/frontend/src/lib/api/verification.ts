/**
 * GTM contact verification HTTP (STORY-11-06 / FE-S11-06).
 * Tip MemVerificationConnector (fake_verify). Not Production GO / RAG GO.
 */
import api from "./client";

const BASE = "/api/v1/gtm/verification";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface VerificationBody {
  email?: string;
  phone?: string;
  provider_key?: string;
  id?: string;
}

export interface ChannelVerdict {
  channel: string;
  value: string;
  status: string;
  confidence: number;
  reason: string;
}

export interface VerificationRun {
  id: string;
  tenant_id: string;
  request: {
    email?: string;
    phone?: string;
    provider_key?: string;
  };
  verdicts: ChannelVerdict[];
  provider_key: string;
  overall_status: string;
  schema_version: number;
  created_at?: string;
}

export interface VerificationMeta {
  channels: string[];
  statuses: string[];
  connectors_configured: string[];
  interface: string;
  honesty: string;
}

export async function getVerificationMeta(tenantId: string): Promise<VerificationMeta> {
  const resp = await api.get<VerificationMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listVerificationRuns(tenantId: string): Promise<VerificationRun[]> {
  const resp = await api.get<VerificationRun[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getVerificationRun(
  tenantId: string,
  runId: string
): Promise<VerificationRun> {
  const resp = await api.get<VerificationRun>(`${BASE}/${runId}`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function runVerification(
  tenantId: string,
  body: VerificationBody
): Promise<VerificationRun> {
  const resp = await api.post<VerificationRun>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
