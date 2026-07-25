import api from"./client";
import type { ActivityQueryResponse, EntityActivityResponse, ActivityRecord } from"./types";

export async function getEntityActivities(
 entityType: string,
 entityId: string,
 tenantId: string,
 limit = 50,
 offset = 0
): Promise<EntityActivityResponse> {
 const response = await api.get(`/api/v1/activities/${entityType}/${entityId}`, {
 params: { limit, offset },
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function getGlobalActivities(
 tenantId: string,
 params: { actor?: string; action?: string; entity_type?: string; limit?: number; offset?: number } = {}
): Promise<ActivityQueryResponse> {
 const response = await api.get("/api/v1/activities", {
 params,
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}

export async function queryActivities(
 params: Record<string, string | number | undefined>,
 tenantId: string
): Promise<ActivityQueryResponse> {
 const response = await api.get("/api/v1/activities", {
 params,
 headers: {"X-Tenant-Id": tenantId },
 });
 return response.data;
}
