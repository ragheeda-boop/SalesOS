/**
 * Studio Prompt Library HTTP (STORY-12-01 / FE-S12-01).
 * Tip in-memory CAP-089. feature_ai_copilot remains False.
 * No live LLM / RAG GO. Not Production GO.
 */
import api from "./client";

const BASE = "/api/v1/studio/prompt-library";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export interface PromptVersionRecord {
  version: string;
  template: string;
  system: string;
  changelog: string;
  created_at?: string;
}

export interface PromptLibraryEntry {
  id: string;
  tenant_id: string;
  name: string;
  key: string;
  active_version: string;
  versions: PromptVersionRecord[];
  domain: string;
  category: string;
  schema_version: number;
  created_at?: string;
  updated_at?: string;
  version_count: number;
}

export interface PromptLibraryMeta {
  object: string;
  capability: string;
  extends: string;
  operations: string[];
  feature_ai_copilot: boolean;
  honesty: string;
}

export interface PromptCreateBody {
  name: string;
  key: string;
  template: string;
  system?: string;
  version?: string;
  changelog?: string;
  domain?: string;
  category?: string;
  id?: string;
}

export interface PromptVersionBody {
  template: string;
  version: string;
  system?: string;
  changelog?: string;
  activate?: boolean;
}

export interface PromptRollbackBody {
  version: string;
}

export interface PromptMetaPatchBody {
  name?: string;
  domain?: string;
  category?: string;
}

export async function getPromptLibraryMeta(
  tenantId: string,
): Promise<PromptLibraryMeta> {
  const resp = await api.get<PromptLibraryMeta>(`${BASE}/meta`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listPromptLibrary(
  tenantId: string,
): Promise<PromptLibraryEntry[]> {
  const resp = await api.get<PromptLibraryEntry[]>(BASE, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getPromptLibraryEntry(
  tenantId: string,
  entryId: string,
): Promise<PromptLibraryEntry> {
  const resp = await api.get<PromptLibraryEntry>(
    `${BASE}/${encodeURIComponent(entryId)}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function createPromptLibraryEntry(
  tenantId: string,
  body: PromptCreateBody,
): Promise<PromptLibraryEntry> {
  const resp = await api.post<PromptLibraryEntry>(BASE, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function patchPromptLibraryMeta(
  tenantId: string,
  entryId: string,
  body: PromptMetaPatchBody,
): Promise<PromptLibraryEntry> {
  const resp = await api.patch<PromptLibraryEntry>(
    `${BASE}/${encodeURIComponent(entryId)}`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function addPromptLibraryVersion(
  tenantId: string,
  entryId: string,
  body: PromptVersionBody,
): Promise<PromptLibraryEntry> {
  const resp = await api.post<PromptLibraryEntry>(
    `${BASE}/${encodeURIComponent(entryId)}/versions`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function rollbackPromptLibrary(
  tenantId: string,
  entryId: string,
  body: PromptRollbackBody,
): Promise<PromptLibraryEntry> {
  const resp = await api.post<PromptLibraryEntry>(
    `${BASE}/${encodeURIComponent(entryId)}/rollback`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function deletePromptLibraryEntry(
  tenantId: string,
  entryId: string,
): Promise<{ deleted: boolean; id: string }> {
  const resp = await api.delete<{ deleted: boolean; id: string }>(
    `${BASE}/${encodeURIComponent(entryId)}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}
