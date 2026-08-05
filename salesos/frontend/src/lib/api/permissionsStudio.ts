/**
 * Tenant Studio permissions HTTP (STORY-10-06 / FE-S10-06).
 * Tip in-memory custom roles capped at Plan.entitlements ceiling.
 * Not Production GO / RAG GO. Does not mutate Owner /admin/roles.
 */
import api from "./client";
import type {
  CeilingCheckRequest,
  CeilingCheckResponse,
  CustomRole,
  CustomRoleUpsert,
  PermissionsCeilingSummary,
  SetPermissionsCeilingBody,
  StudioPermissionCatalogItem,
} from "./types/tenantStudio";

const BASE = "/api/v1/studio/permissions";

function tenantHeaders(tenantId: string) {
  return { "X-Tenant-Id": tenantId };
}

export async function listPermissionsCatalog(
  tenantId: string,
  planTier?: string | null
): Promise<StudioPermissionCatalogItem[]> {
  const resp = await api.get<StudioPermissionCatalogItem[]>(`${BASE}/catalog`, {
    headers: tenantHeaders(tenantId),
    params: planTier ? { plan_tier: planTier } : undefined,
  });
  return resp.data;
}

export async function getPermissionsCeiling(
  tenantId: string,
  planTier?: string | null
): Promise<PermissionsCeilingSummary> {
  const resp = await api.get<PermissionsCeilingSummary>(`${BASE}/ceiling`, {
    headers: tenantHeaders(tenantId),
    params: planTier ? { plan_tier: planTier } : undefined,
  });
  return resp.data;
}

export async function setPermissionsCeiling(
  tenantId: string,
  body: SetPermissionsCeilingBody
): Promise<PermissionsCeilingSummary> {
  const resp = await api.put<PermissionsCeilingSummary>(`${BASE}/ceiling`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function checkPermissionsCeiling(
  tenantId: string,
  body: CeilingCheckRequest
): Promise<CeilingCheckResponse> {
  const resp = await api.post<CeilingCheckResponse>(`${BASE}/check`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function listCustomRoles(tenantId: string): Promise<CustomRole[]> {
  const resp = await api.get<CustomRole[]>(`${BASE}/roles`, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}

export async function upsertCustomRole(
  tenantId: string,
  body: CustomRoleUpsert
): Promise<CustomRole> {
  const resp = await api.post<CustomRole>(`${BASE}/roles`, body, {
    headers: tenantHeaders(tenantId),
  });
  return resp.data;
}
