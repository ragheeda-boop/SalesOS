import api from "./client";
import type {
  ActivityDashboardDTO,
  CompanyEngagementDTO,
  EmailMetricsDTO,
  CalendarMetricsDTO,
  FollowupDashboardDTO,
  EngagementSummaryDTO,
} from "./types";

export async function getActivityDashboard(tenantId: string): Promise<ActivityDashboardDTO> {
  const response = await api.get("/api/v1/activity/dashboard", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getCompanyEngagement(
  companyId: string,
  tenantId: string
): Promise<CompanyEngagementDTO> {
  const response = await api.get(`/api/v1/activity/company/${companyId}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEmailMetrics(tenantId: string): Promise<EmailMetricsDTO> {
  const response = await api.get("/api/v1/activity/email", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getCalendarMetrics(tenantId: string): Promise<CalendarMetricsDTO> {
  const response = await api.get("/api/v1/activity/calendar", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getFollowups(tenantId: string): Promise<FollowupDashboardDTO> {
  const response = await api.get("/api/v1/activity/followups", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getEngagementSummary(tenantId: string): Promise<EngagementSummaryDTO> {
  const response = await api.get("/api/v1/activity/engagement", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
