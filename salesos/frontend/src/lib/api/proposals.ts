import api from "./client";

/** List row from GET /api/v1/proposals — empty unless opportunity_id is set. */
export interface ProposalListItem {
  id: string;
  status: string;
  opportunity_id: string;
  title: string;
}

export interface ProposalListResponse {
  items: ProposalListItem[];
  total: number;
}

export async function listProposals(
  params?: { opportunity_id?: string },
  tenantId?: string
): Promise<ProposalListResponse> {
  const response = await api.get("/api/v1/proposals", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

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
