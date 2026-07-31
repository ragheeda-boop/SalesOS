import client from "./client";
import type { ApiKeyRecord, NotificationPreferences } from "./types";

export async function getApiKeys(tenantId: string): Promise<ApiKeyRecord[]> {
  const response = await client.get("/api/v1/settings/api-keys", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function createApiKey(
  name: string,
  tenantId: string,
): Promise<{ key: string; record: ApiKeyRecord }> {
  const response = await client.post(
    "/api/v1/settings/api-keys",
    { name },
    {
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function deleteApiKey(
  id: string,
  tenantId: string,
): Promise<void> {
  await client.delete(`/api/v1/settings/api-keys/${id}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
}

export async function getNotificationPreferences(
  tenantId: string,
): Promise<NotificationPreferences> {
  const response = await client.get("/api/v1/settings/notifications", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function updateNotificationPreferences(
  data: Partial<NotificationPreferences>,
  tenantId: string,
): Promise<NotificationPreferences> {
  const response = await client.patch("/api/v1/settings/notifications", data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
