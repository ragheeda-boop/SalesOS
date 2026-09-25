import api from "./client";
import type {
  CreatePipelineResponse,
  DealIntelligence,
  ExecutiveDashboardResponse,
  Opportunity,
  OpportunityNBA,
  OpportunityListResponse,
  PipelineAnalyticsSummary,
  PipelineListResponse,
  RecommendationsResponse,
} from "./types";

export async function getRecommendations(tenantId: string): Promise<RecommendationsResponse> {
  const response = await api.get("/api/v1/recommendations", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function getOpportunityNBA(
  opportunityId: string,
  tenantId: string
): Promise<OpportunityNBA> {
  const response = await api.get(`/api/v1/opportunities/${encodeURIComponent(opportunityId)}/nba`, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function refreshOpportunityNBA(
  opportunityId: string,
  tenantId: string
): Promise<OpportunityNBA> {
  const response = await api.post(
    `/api/v1/opportunities/${encodeURIComponent(opportunityId)}/nba/refresh`,
    null,
    { headers: { "X-Tenant-Id": tenantId } }
  );
  return response.data;
}

export async function getDealIntelligence(
  opportunityId: string,
  tenantId: string
): Promise<DealIntelligence> {
  const response = await api.get(
    `/api/v1/opportunities/${encodeURIComponent(opportunityId)}/intelligence`,
    { headers: { "X-Tenant-Id": tenantId } }
  );
  return response.data;
}

export async function getPipelineAnalyticsSummary(
  tenantId: string
): Promise<PipelineAnalyticsSummary> {
  const response = await api.get("/api/v1/pipeline/summary", {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

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

/** POST /api/v1/pipelines — no body. Server creates the default sales pipeline. */
export async function createPipeline(tenantId: string): Promise<CreatePipelineResponse> {
  const response = await api.post("/api/v1/pipelines", null, {
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
