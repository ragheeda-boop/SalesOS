import api from "./client";
import type {
  ExecutiveDashboardResponse,
  Opportunity,
  OpportunityListResponse,
  PipelineListResponse,
} from "./types";

export async function getExecutiveDashboard(tenantId: string): Promise<ExecutiveDashboardResponse> {
  const response = await api.get("/api/v1/executive/dashboard", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function listOpportunities(tenantId: string): Promise<OpportunityListResponse> {
  const response = await api.get("/api/v1/opportunities", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getOpportunity(
  opportunityId: string,
  tenantId: string
): Promise<Opportunity> {
  const response = await api.get(`/api/v1/opportunities/${opportunityId}`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function createOpportunity(
  tenantId: string,
  companyId: string,
  name: string,
  value = 0
) {
  const response = await api.post("/api/v1/opportunities", null, {
    params: { company_id: companyId, name, value },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function advanceOpportunity(opportunityId: string, toStage: string) {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/advance`, null, {
    params: { to_stage: toStage },
  });
  return response.data;
}

export async function closeWon(opportunityId: string, amount?: number) {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/won`, null, {
    params: amount ? { amount } : undefined,
  });
  return response.data;
}

export async function closeLost(opportunityId: string, reason = "") {
  const response = await api.post(`/api/v1/opportunities/${opportunityId}/lost`, null, {
    params: reason ? { reason } : undefined,
  });
  return response.data;
}

export async function listPipelines(tenantId: string): Promise<PipelineListResponse> {
  const response = await api.get("/api/v1/pipelines", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
