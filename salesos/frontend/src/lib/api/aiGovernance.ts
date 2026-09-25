import api from "./client";
import type { AIGovernanceAuditResponse } from "./types/aiGovernance";

export async function listAIGovernanceAudit(
  tenantId: string,
  params: { page?: number; page_size?: number } = {}
): Promise<AIGovernanceAuditResponse> {
  const response = await api.get<AIGovernanceAuditResponse>("/api/v1/ai-governance/audit", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
