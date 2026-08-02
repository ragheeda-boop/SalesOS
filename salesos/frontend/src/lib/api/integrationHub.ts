/**
 * Integration Hub HTTP client (DOM-021).
 * Tip endpoints only (STORY-08-06 / FE-S08-08 conflict-policy). Not Production GO.
 */
import api from "./client";
import type {
  HubConflictPolicy,
  HubConflictPolicyUpsert,
  HubConnection,
  HubConnectionCreate,
  HubConnectionTestResult,
  HubDisconnectResult,
  HubMapping,
  HubMappingCreate,
  HubScheduleCreate,
  HubScheduleResult,
  HubSyncRun,
} from "./types/integrationHub";

const BASE = "/api/v1/integrations";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listHubConnections(
  tenantId: string,
  limit = 100,
): Promise<HubConnection[]> {
  const resp = await api.get<HubConnection[]>(`${BASE}/connections`, {
    headers: tenantHeaders(tenantId),
    params: { limit },
  });
  return resp.data;
}

export async function createHubConnection(
  tenantId: string,
  body: HubConnectionCreate,
): Promise<HubConnection> {
  const resp = await api.post<HubConnection>(`${BASE}/connections`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function getHubConnection(
  tenantId: string,
  connectionId: string,
): Promise<HubConnection> {
  const resp = await api.get<HubConnection>(
    `${BASE}/connections/${connectionId}`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function testHubConnection(
  tenantId: string,
  connectionId: string,
): Promise<HubConnectionTestResult> {
  const resp = await api.post<HubConnectionTestResult>(
    `${BASE}/connections/${connectionId}/test`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function disconnectHubConnection(
  tenantId: string,
  connectionId: string,
): Promise<HubDisconnectResult> {
  const resp = await api.post<HubDisconnectResult>(
    `${BASE}/connections/${connectionId}/disconnect`,
    {},
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function createHubMapping(
  tenantId: string,
  connectionId: string,
  body: HubMappingCreate,
): Promise<HubMapping> {
  const resp = await api.post<HubMapping>(
    `${BASE}/connections/${connectionId}/mappings`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function getActiveHubMapping(
  tenantId: string,
  connectionId: string,
  model: string,
): Promise<HubMapping | null> {
  const resp = await api.get<HubMapping | null>(
    `${BASE}/connections/${connectionId}/mappings/active`,
    {
      headers: tenantHeaders(tenantId),
      params: { model },
    },
  );
  return resp.data;
}

export async function getHubConflictPolicy(
  tenantId: string,
  connectionId: string,
): Promise<HubConflictPolicy> {
  const resp = await api.get<HubConflictPolicy>(
    `${BASE}/connections/${connectionId}/conflict-policy`,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function putHubConflictPolicy(
  tenantId: string,
  connectionId: string,
  body: HubConflictPolicyUpsert,
): Promise<HubConflictPolicy> {
  const resp = await api.put<HubConflictPolicy>(
    `${BASE}/connections/${connectionId}/conflict-policy`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function scheduleHubSync(
  tenantId: string,
  connectionId: string,
  body: HubScheduleCreate,
): Promise<HubScheduleResult> {
  const resp = await api.post<HubScheduleResult>(
    `${BASE}/connections/${connectionId}/schedule`,
    body,
    { headers: tenantHeaders(tenantId) },
  );
  return resp.data;
}

export async function listHubSyncRuns(
  tenantId: string,
  connectionId: string,
  limit = 50,
): Promise<HubSyncRun[]> {
  const resp = await api.get<HubSyncRun[]>(
    `${BASE}/connections/${connectionId}/sync-runs`,
    {
      headers: tenantHeaders(tenantId),
      params: { limit },
    },
  );
  return resp.data;
}
