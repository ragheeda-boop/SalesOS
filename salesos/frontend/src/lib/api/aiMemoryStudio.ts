/**
 * Studio AI Memory HTTP (STORY-12-03 / FE-S12-03).
 * Tip in-memory CAP-063 conversation-level MVP.
 * feature_ai_copilot remains False. No live LLM / RAG GO. Not Production GO.
 */
import api from "./client";

const BASE = "/api/v1/studio/ai-memory";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface MemoryTurn {
  role: string;
  content: string;
  created_at?: string;
  encryption?: Record<string, string>;
}

export interface ConversationMemory {
  id: string;
  tenant_id: string;
  conversation_id: string;
  turns: MemoryTurn[];
  turn_count: number;
  provider_cache_key: string;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
  scope: string;
}

export interface MemorySettings {
  tenant_id: string;
  enabled: boolean;
  max_turns: number;
  retention_hours: number;
  updated_at?: string;
  opt_in: boolean;
  cross_session: boolean;
  feature_ai_copilot: boolean;
}

export interface AiMemoryMeta {
  object: string;
  capability: string;
  scope: string;
  cross_session: boolean;
  opt_in_default: boolean;
  retention_policy: string;
  provider_cache: string;
  encryption: string;
  deletion_policy: string;
  policy_count_delta: number;
  feature_ai_copilot: boolean;
  honesty: string;
}

export interface MemorySettingsBody {
  enabled: boolean;
  max_turns: number;
  retention_hours: number;
}

export interface MemoryTurnBody {
  role: string;
  content: string;
}

export interface AdversarialProbeBody {
  owner_tenant_id: string;
  attacker_tenant_id: string;
  conversation_id: string;
}

export async function getAiMemoryMeta(tenantId: string): Promise<AiMemoryMeta> {
  const resp = await api.get<AiMemoryMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getAiMemorySettings(
  tenantId: string,
): Promise<MemorySettings> {
  const resp = await api.get<MemorySettings>(`${BASE}/settings`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function putAiMemorySettings(
  tenantId: string,
  body: MemorySettingsBody,
): Promise<MemorySettings> {
  const resp = await api.put<MemorySettings>(`${BASE}/settings`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listAiMemoryConversations(
  tenantId: string,
): Promise<ConversationMemory[]> {
  const resp = await api.get<ConversationMemory[]>(`${BASE}/conversations`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getAiMemoryConversation(
  tenantId: string,
  conversationId: string,
): Promise<ConversationMemory> {
  const resp = await api.get<ConversationMemory>(
    `${BASE}/conversations/${conversationId}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function appendAiMemoryTurn(
  tenantId: string,
  conversationId: string,
  body: MemoryTurnBody,
): Promise<ConversationMemory> {
  const resp = await api.post<ConversationMemory>(
    `${BASE}/conversations/${conversationId}/turns`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function deleteAiMemoryConversation(
  tenantId: string,
  conversationId: string,
): Promise<{ deleted: boolean; conversation_id: string }> {
  const resp = await api.delete<{ deleted: boolean; conversation_id: string }>(
    `${BASE}/conversations/${conversationId}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function probeAiMemoryAdversarial(
  tenantId: string,
  body: AdversarialProbeBody,
): Promise<Record<string, unknown>> {
  const resp = await api.post<Record<string, unknown>>(
    `${BASE}/adversarial/probe`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
