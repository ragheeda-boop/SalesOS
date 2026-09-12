import api from "./client";

/** 201 payload from POST /api/v1/proposals — not a full proposal record. */
export interface CreateProposalResponse {
  id: string;
  status: string;
  sections: number;
}

/**
 * POST /api/v1/proposals — query `opportunity_id` + `quote_id` required.
 * Null body. Matches FastAPI Query(...) (same pattern as createQuote).
 */
export async function createProposal(
  tenantId: string,
  opportunityId: string,
  quoteId: string
): Promise<CreateProposalResponse> {
  const response = await api.post("/api/v1/proposals", null, {
    params: { opportunity_id: opportunityId, quote_id: quoteId },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}
