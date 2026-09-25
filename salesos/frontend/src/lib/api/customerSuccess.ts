import api from "./client";

export type SurveyType = "nps" | "csat";

export interface CustomerSurveyResponse {
  id: string;
  tenant_id: string;
  company_id: string;
  survey_type: SurveyType;
  score: number;
  comment: string | null;
  source: string;
  recorded_at: string;
  created_at: string;
}

export interface CustomerSurveySummary {
  company_id: string | null;
  nps: number | null;
  nps_responses: number;
  promoters: number;
  detractors: number;
  csat_average: number | null;
  csat_responses: number;
  response_rate: number | null;
  response_rate_reason: string;
}

function tenantHeaders(tenantId?: string) {
  return tenantId ? { "X-Tenant-Id": tenantId } : undefined;
}

export async function getCustomerSurveySummary(
  tenantId?: string,
  companyId?: string
): Promise<CustomerSurveySummary> {
  const response = await api.get("/api/v1/customer-success/surveys/summary", {
    params: companyId ? { company_id: companyId } : undefined,
    headers: tenantHeaders(tenantId),
  });
  return response.data;
}

export async function recordCustomerSurveyResponse(
  input: {
    company_id: string;
    survey_type: SurveyType;
    score: number;
    comment?: string;
    source?: "manual" | "import";
    idempotency_key?: string;
  },
  tenantId?: string
): Promise<CustomerSurveyResponse> {
  const response = await api.post("/api/v1/customer-success/surveys", input, {
    headers: tenantHeaders(tenantId),
  });
  return response.data;
}
