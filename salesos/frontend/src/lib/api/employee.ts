import api from "./client";
import type {
  BulkEditEmployeesRequest,
  CalendarHeatmapPoint,
  CalendarKPIsResponse,
  CursorResponse,
  DailyVolumePoint,
  EmailKPIsResponse,
  EmployeeListItem,
  EmployeePerformanceResponse,
  EmployeeSearchParams,
  EmployeeScoreResponse,
  EmployeeSignalsResponse,
  EmployeeTimelineParams,
  EmployeeTimelineResponse,
  Employee360Response,
  ExecutiveSummaryResponse,
  ProductivityResponse,
  RelationshipScoreResponse,
  TopContactItem,
} from "./types";

export async function getEmployee360(
  id: string,
  tenantId: string,
): Promise<Employee360Response> {
  const response = await api.get(`/api/v1/employees/${id}/360`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getMy360(tenantId: string): Promise<Employee360Response> {
  const response = await api.get("/api/v1/employees/me/360", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function searchEmployees(
  params: EmployeeSearchParams,
  tenantId: string,
): Promise<CursorResponse<EmployeeListItem>> {
  const response = await api.get("/api/v1/employees", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmployeeSignals(
  employeeId: string,
  tenantId: string,
): Promise<EmployeeSignalsResponse> {
  const response = await api.get(`/api/v1/employees/${employeeId}/signals`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmployeeScore(
  employeeId: string,
  tenantId: string,
): Promise<EmployeeScoreResponse> {
  const response = await api.get(`/api/v1/employees/${employeeId}/score`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmployeeTimeline(
  employeeId: string,
  params: EmployeeTimelineParams,
  tenantId: string,
): Promise<EmployeeTimelineResponse> {
  const response = await api.get(`/api/v1/employees/${employeeId}/timeline`, {
    params: {
      ...params,
      source: params.source?.join(","),
      type: params.type?.join(","),
    },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmployeePerformance(
  employeeId: string,
  tenantId: string,
): Promise<EmployeePerformanceResponse> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/performance`,
    {
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function bulkEditEmployees(
  data: BulkEditEmployeesRequest,
  tenantId: string,
): Promise<{ updated: number }> {
  const response = await api.patch("/api/v1/employees/bulk", data, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function bulkDeleteEmployees(
  ids: string[],
  tenantId: string,
): Promise<{ deleted: number }> {
  const response = await api.post(
    "/api/v1/employees/bulk-delete",
    { ids },
    {
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function exportEmployees(
  params: Record<string, unknown>,
  tenantId: string,
): Promise<Blob> {
  const searchParams = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "" && v !== null)
      searchParams.set(k, String(v));
  });
  searchParams.set("format", "csv");
  const response = await api.get(
    `/api/v1/employees/export?${searchParams.toString()}`,
    {
      headers: { "X-Tenant-Id": tenantId },
      responseType: "blob",
    },
  );
  return response.data;
}

export async function getEmployeeCalendarKPIs(
  employeeId: string,
  tenantId: string,
): Promise<CalendarKPIsResponse> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/calendar-kpis`,
    {
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function getEmployeeCalendarHeatmap(
  employeeId: string,
  tenantId: string,
  days: number = 30,
): Promise<CalendarHeatmapPoint[]> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/calendar-heatmap`,
    {
      params: { days },
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function getEmployeeEmailKPIs(
  employeeId: string,
  tenantId: string,
  days: number = 30,
): Promise<EmailKPIsResponse> {
  const response = await api.get(`/api/v1/employees/${employeeId}/email-kpis`, {
    params: { days },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmployeeEmailTopContacts(
  employeeId: string,
  tenantId: string,
  limit: number = 10,
): Promise<TopContactItem[]> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/email-top-contacts`,
    {
      params: { limit },
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function getEmployeeEmailDailyVolume(
  employeeId: string,
  tenantId: string,
  days: number = 30,
): Promise<DailyVolumePoint[]> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/email-daily-volume`,
    {
      params: { days },
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function getEmployeeProductivity(
  employeeId: string,
  tenantId: string,
  periodDays: number = 30,
): Promise<ProductivityResponse> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/productivity`,
    {
      params: { period_days: periodDays },
      headers: { "X-Tenant-Id": tenantId },
    },
  );
  return response.data;
}

export async function getEmployeeRelationshipScore(
  employeeId: string,
  targetType: string,
  targetId: string,
  tenantId: string,
): Promise<RelationshipScoreResponse> {
  const response = await api.get(
    `/api/v1/employees/${employeeId}/relationship/${targetType}/${targetId}`,
    { headers: { "X-Tenant-Id": tenantId } },
  );
  return response.data;
}

export async function getExecutiveSummary(
  tenantId: string,
): Promise<ExecutiveSummaryResponse> {
  const response = await api.get("/api/v1/executive/summary", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
