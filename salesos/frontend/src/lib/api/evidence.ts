import api from "./client";
import type { CommercialEvidenceResponse } from "./types/evidence";

export async function listCommercialEvidence(
  tenantId: string,
  params: {
    page?: number;
    page_size?: number;
    target_type?: string;
    target_id?: string;
    category?: string;
  } = {}
): Promise<CommercialEvidenceResponse> {
  const response = await api.get<CommercialEvidenceResponse>("/api/v1/evidence/insights", {
    params,
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
