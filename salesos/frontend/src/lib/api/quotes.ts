import api from "./client";

export interface QuoteLine {
  id: string;
  description: string;
  description_ar?: string;
  quantity: number;
  unit_price: number;
  discount_percent: number;
  tax_percent: number;
  product_code?: string;
  notes?: string;
  line_total: number;
  discount_amount: number;
  net_total: number;
  tax_amount: number;
  grand_total: number;
}

export interface ApprovalState {
  level: string;
  approved_by?: string;
  approved_at?: string;
  comments?: string;
}

export interface QuoteRevision {
  version: number;
  quote_id: string;
  status: string;
  lines: QuoteLine[];
  subtotal: number;
  total_discount: number;
  total_tax: number;
  grand_total: number;
  notes?: string;
  created_at: string;
}

export interface Quote {
  id: string;
  tenant_id: string;
  opportunity_id: string;
  company_id?: string;
  title: string;
  status: string;
  version: number;
  lines: QuoteLine[];
  revisions: QuoteRevision[];
  approval: ApprovalState;
  currency: string;
  payment_terms?: string;
  delivery_terms?: string;
  valid_until?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  created_by?: string;
  subtotal: number;
  total_discount: number;
  total_tax: number;
  grand_total: number;
}

export interface QuoteListResponse {
  items: Quote[];
  total: number;
}

export async function listQuotes(
  params?: { opportunity_id?: string; status?: string; page?: number; page_size?: number },
  tenantId?: string
): Promise<QuoteListResponse> {
  const response = await api.get("/api/v1/quotes", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getQuote(quoteId: string, tenantId?: string): Promise<Quote> {
  const response = await api.get(`/api/v1/quotes/${quoteId}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

/** 201 payload from POST /api/v1/quotes — not the full Quote record. */
export interface CreateQuoteResponse {
  id: string;
  title: string;
  status: string;
  version: number;
}

/**
 * POST /api/v1/quotes — query `opportunity_id` required; `title` defaults to Quote.
 * Null body. Matches FastAPI Query(...) (same pattern as createOpportunity).
 */
export async function createQuote(
  tenantId: string,
  opportunityId: string,
  title = "Quote"
): Promise<CreateQuoteResponse> {
  const response = await api.post("/api/v1/quotes", null, {
    params: { opportunity_id: opportunityId, title },
    headers: { "X-Tenant-Id": tenantId },
  });
  return response.data;
}

export async function addQuoteLine(
  quoteId: string,
  data: { description: string; quantity: number; unit_price: number; discount_percent?: number; tax_percent?: number; product_code?: string; notes?: string },
  tenantId?: string
): Promise<QuoteLine> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/lines`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function submitQuote(quoteId: string, tenantId?: string): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/submit`, undefined, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function approveQuote(
  quoteId: string,
  data: { approved_by: string; approval_level: string; comments?: string },
  tenantId?: string
): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/approve`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function sendQuote(quoteId: string, tenantId?: string): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/send`, undefined, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function acceptQuote(quoteId: string, tenantId?: string): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/accept`, undefined, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function rejectQuote(
  quoteId: string,
  data: { reason: string },
  tenantId?: string
): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/reject`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function reviseQuote(
  quoteId: string,
  data?: { notes?: string },
  tenantId?: string
): Promise<Quote> {
  const response = await api.post(`/api/v1/quotes/${quoteId}/revise`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}
