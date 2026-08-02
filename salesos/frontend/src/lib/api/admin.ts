import api from "./client";
import type {
  AdminAICost,
  AdminAICostSummary,
  AdminAIUsage,
  AdminConfigResponse,
  AdminDetailedHealth,
  AdminFeatureFlag,
  AdminFlagTenant,
  AdminHealthHistoryEntry,
  AdminInvoice,
  AdminJob,
  AdminJobDetail,
  AdminLicense,
  AdminPermission,
  AdminPlan,
  AdminRole,
  AdminTenantCreate,
  AdminTenantDetail,
  AdminTenantListItem,
  AdminTenantActivateRequest,
  AdminTenantActivateResponse,
  AdminTenantHardDeleteRequest,
  AdminTenantHardDeleteResponse,
  AdminTenantSoftDeleteResponse,
  AdminTenantSuspendRequest,
  AdminTenantSuspendResponse,
  AdminTenantUpdate,
  AdminTenantUsage,
  AdminTransaction,
  AdminUser,
  AdminUserDetail,
  AuditLogEntry,
  CopilotFeedbackRequest,
  CopilotFeedbackResponse,
  CopilotTelemetryData,
  DlqEntry,
  DlqRetryResponse,
  EntityResolutionConflict,
  FullHealthResponse,
  GoldenRecordAdmin,
  PaginatedResponse,
  TaskResponse,
} from "./types";

export async function getAdminHealth(
  tenantId: string,
): Promise<FullHealthResponse> {
  const response = await api.get("/health/full", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getAdminMetrics(tenantId: string): Promise<string> {
  const response = await api.get("/api/v1/admin/metrics", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listGoldenRecords(
  tenantId: string,
  params: { page?: number; page_size?: number; status?: string } = {},
): Promise<PaginatedResponse<GoldenRecordAdmin>> {
  const response = await api.get("/api/v1/entity-resolution/golden-records", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listConflicts(
  tenantId: string,
  params: { page?: number; page_size?: number; status?: string } = {},
): Promise<PaginatedResponse<EntityResolutionConflict>> {
  const response = await api.get("/api/v1/entity-resolution/conflicts", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listDlq(
  tenantId: string,
  params: {
    page?: number;
    page_size?: number;
    status?: string;
    stage?: string;
  } = {},
): Promise<PaginatedResponse<DlqEntry>> {
  const response = await api.get("/api/v1/admin/dlq", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function retryDlq(
  tenantId: string,
  limit = 50,
): Promise<DlqRetryResponse> {
  const response = await api.post("/api/v1/admin/dlq/retry", null, {
    params: { limit },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function purgeDlq(
  tenantId: string,
  status?: string,
): Promise<{ purged: number }> {
  const response = await api.delete("/api/v1/admin/dlq", {
    params: status ? { status } : undefined,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getDlqStats(
  tenantId: string,
): Promise<{ failed_by_stage: Record<string, number> }> {
  const response = await api.get("/api/v1/admin/dlq/stats", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listTasks(
  tenantId: string,
  priority?: string,
): Promise<TaskResponse[]> {
  const response = await api.get("/api/v1/tasks", {
    params: priority ? { priority } : undefined,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function completeTask(taskId: string): Promise<TaskResponse> {
  const response = await api.put(`/api/v1/tasks/${taskId}/complete`);
  return response.data;
}

export async function createTask(
  tenantId: string,
  title: string,
  priority?: string,
  companyId?: string,
  source?: string,
): Promise<TaskResponse> {
  const response = await api.post(
    "/api/v1/tasks",
    { title, priority, company_id: companyId, source },
    { headers: { "X-Tenant-Id": tenantId } },
  );
  return response.data;
}

export async function listAdminTenants(
  params?: Record<string, string | undefined>,
): Promise<AdminTenantListItem[]> {
  const resp = await api.get("/api/v1/admin/tenants", { params });
  return resp.data;
}

export async function createAdminTenant(
  data: AdminTenantCreate,
): Promise<AdminTenantDetail> {
  const resp = await api.post("/api/v1/admin/tenants", data);
  return resp.data;
}

export async function getAdminTenant(id: string): Promise<AdminTenantDetail> {
  const resp = await api.get(`/api/v1/admin/tenants/${id}`);
  return resp.data;
}

export async function updateAdminTenant(
  id: string,
  data: AdminTenantUpdate,
): Promise<AdminTenantDetail> {
  const resp = await api.put(`/api/v1/admin/tenants/${id}`, data);
  return resp.data;
}

/** FE-S04-09 — soft-delete (is_active=false); not permanent. */
export async function deleteAdminTenant(
  id: string,
): Promise<AdminTenantSoftDeleteResponse> {
  const resp = await api.delete(`/api/v1/admin/tenants/${id}`);
  return resp.data;
}

/** Alias for honesty in call sites. */
export const softDeleteAdminTenant = deleteAdminTenant;

/** FE-S04-11 — hard-delete requires confirm: true. */
export async function hardDeleteAdminTenant(
  id: string,
  data: AdminTenantHardDeleteRequest,
): Promise<AdminTenantHardDeleteResponse> {
  const resp = await api.delete(`/api/v1/admin/tenants/${id}/hard-delete`, {
    data,
  });
  return resp.data;
}

/** FE-S04-06 — suspend sets is_active=false + provisioning_status=suspended. */
export async function suspendAdminTenant(
  id: string,
  data: AdminTenantSuspendRequest = {},
): Promise<AdminTenantSuspendResponse> {
  const resp = await api.post(`/api/v1/admin/tenants/${id}/suspend`, {
    reason: data.reason ?? "",
  });
  return resp.data;
}

/** FE-S04-27 — activate via POST /activate (tip d9d1472); not PUT is_active. */
export async function activateAdminTenant(
  id: string,
  data: AdminTenantActivateRequest = {},
): Promise<AdminTenantActivateResponse> {
  const resp = await api.post(`/api/v1/admin/tenants/${id}/activate`, {
    reason: data.reason ?? "",
  });
  return resp.data;
}

export async function getAdminTenantUsage(
  id: string,
): Promise<AdminTenantUsage> {
  const resp = await api.get(`/api/v1/admin/tenants/${id}/usage`);
  return resp.data;
}

export async function listAdminPlans(): Promise<AdminPlan[]> {
  const resp = await api.get("/api/v1/admin/plans");
  return resp.data;
}

export async function createAdminPlan(
  data: Record<string, unknown>,
): Promise<AdminPlan> {
  const resp = await api.post("/api/v1/admin/plans", data);
  return resp.data;
}

export async function updateAdminPlan(
  id: string,
  data: Record<string, unknown>,
): Promise<AdminPlan> {
  const resp = await api.put(`/api/v1/admin/plans/${id}`, data);
  return resp.data;
}

export async function listAdminLicenses(): Promise<AdminLicense[]> {
  const resp = await api.get("/api/v1/admin/licenses");
  return resp.data;
}

export async function createAdminLicense(data: {
  tenant_id: string;
  plan_id: string;
}): Promise<AdminLicense> {
  const resp = await api.post("/api/v1/admin/licenses", data);
  return resp.data;
}

export async function listAdminUsers(
  params?: Record<string, string | undefined>,
): Promise<AdminUser[]> {
  const resp = await api.get("/api/v1/admin/users", { params });
  return resp.data;
}

export async function getAdminUser(id: string): Promise<AdminUserDetail> {
  const resp = await api.get(`/api/v1/admin/users/${id}`);
  return resp.data;
}

export async function updateAdminUser(
  id: string,
  data: Record<string, unknown>,
): Promise<AdminUserDetail> {
  const resp = await api.put(`/api/v1/admin/users/${id}`, data);
  return resp.data;
}

export async function deactivateAdminUser(id: string): Promise<void> {
  await api.delete(`/api/v1/admin/users/${id}`);
}

export async function listAdminInvoices(
  tenantId?: string,
): Promise<AdminInvoice[]> {
  const resp = await api.get("/api/v1/admin/billing/invoices", {
    params: tenantId ? { tenant_id: tenantId } : undefined,
  });
  return resp.data;
}

export async function listAdminTransactions(
  tenantId?: string,
): Promise<AdminTransaction[]> {
  const resp = await api.get("/api/v1/admin/billing/transactions", {
    params: tenantId ? { tenant_id: tenantId } : undefined,
  });
  return resp.data;
}

export async function listAdminFeatureFlags(): Promise<AdminFeatureFlag[]> {
  const resp = await api.get("/api/v1/admin/feature-flags");
  return resp.data;
}

export async function createAdminFeatureFlag(data: {
  key: string;
  name: string;
  description?: string;
  enabled?: boolean;
}): Promise<AdminFeatureFlag> {
  const resp = await api.post("/api/v1/admin/feature-flags", data);
  return resp.data;
}

export async function updateAdminFeatureFlag(
  id: string,
  data: Record<string, unknown>,
): Promise<AdminFeatureFlag> {
  const resp = await api.put(`/api/v1/admin/feature-flags/${id}`, data);
  return resp.data;
}

export async function getAdminFlagTenants(
  id: string,
): Promise<AdminFlagTenant[]> {
  const resp = await api.get(`/api/v1/admin/feature-flags/${id}/tenants`);
  return resp.data;
}

export async function toggleAdminFlagForTenant(
  flagId: string,
  tenantId: string,
  enabled: boolean,
): Promise<void> {
  await api.put(`/api/v1/admin/feature-flags/${flagId}/tenants/${tenantId}`, {
    enabled,
  });
}

export async function listAdminJobs(
  params?: Record<string, string | number | undefined>,
): Promise<AdminJob[]> {
  const resp = await api.get("/api/v1/admin/jobs", { params });
  return resp.data;
}

export async function getAdminJob(id: string): Promise<AdminJobDetail> {
  const resp = await api.get(`/api/v1/admin/jobs/${id}`);
  return resp.data;
}

export async function retryAdminJob(id: string): Promise<void> {
  await api.post(`/api/v1/admin/jobs/${id}/retry`);
}

export async function listAdminAICosts(
  params?: Record<string, string | number | undefined>,
): Promise<AdminAICost[]> {
  const resp = await api.get("/api/v1/admin/ai/costs", { params });
  return resp.data;
}

export async function getAdminAICostSummary(
  days?: number,
): Promise<AdminAICostSummary> {
  const resp = await api.get("/api/v1/admin/ai/summary", {
    params: days ? { days } : undefined,
  });
  return resp.data;
}

export async function getAdminAIUsage(days?: number): Promise<AdminAIUsage> {
  const resp = await api.get("/api/v1/admin/ai/usage", {
    params: days ? { days } : undefined,
  });
  return resp.data;
}

export async function getAdminDetailedHealth(): Promise<AdminDetailedHealth> {
  const resp = await api.get("/api/v1/admin/health/detailed");
  return resp.data;
}

export async function getAdminHealthHistory(
  hours?: number,
): Promise<AdminHealthHistoryEntry[]> {
  const resp = await api.get("/api/v1/admin/health/history", {
    params: hours ? { hours } : undefined,
  });
  return resp.data;
}

export async function listAdminAuditLogs(
  params?: Record<string, string | number | undefined>,
): Promise<PaginatedResponse<AuditLogEntry>> {
  const resp = await api.get("/api/v1/audit/logs", { params });
  return resp.data;
}

export async function listAdminRoles(): Promise<AdminRole[]> {
  const resp = await api.get("/api/v1/admin/roles");
  return resp.data;
}

export async function listAdminPermissions(): Promise<AdminPermission[]> {
  const resp = await api.get("/api/v1/admin/permissions");
  return resp.data;
}

export async function createAdminRole(data: {
  name: string;
  description?: string;
  permissions: string[];
}): Promise<AdminRole> {
  const resp = await api.post("/api/v1/admin/roles", data);
  return resp.data;
}

export async function updateAdminRole(
  id: string,
  data: Record<string, unknown>,
): Promise<AdminRole> {
  const resp = await api.put(`/api/v1/admin/roles/${id}`, data);
  return resp.data;
}

export async function deleteAdminRole(id: string): Promise<void> {
  await api.delete(`/api/v1/admin/roles/${id}`);
}

export async function getAdminConfig(): Promise<AdminConfigResponse> {
  const resp = await api.get("/api/v1/admin/config");
  return resp.data;
}

export async function saveAdminConfig(
  content: string,
): Promise<AdminConfigResponse> {
  const resp = await api.put("/api/v1/admin/config", { content });
  return resp.data;
}

export async function validateAdminConfig(
  content: string,
): Promise<{ valid: boolean; errors: string[] }> {
  const resp = await api.post("/api/v1/admin/config/validate", { content });
  return resp.data;
}

export async function submitCopilotFeedback(
  data: CopilotFeedbackRequest,
  tenantId: string,
): Promise<CopilotFeedbackResponse> {
  const response = await api.post("/api/v1/copilot/feedback", data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getCopilotTelemetry(
  tenantId: string,
  days = 7,
): Promise<CopilotTelemetryData> {
  const response = await api.get("/api/v1/copilot/telemetry", {
    params: { days },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
