// Phase 7-A — Review Queue API client queries.
import apiClient from "@/lib/api/client";
import { getTenantId } from "@/lib/hooks/useTenant";

export type P3Pair = {
  id: string;
  subject_key: string;
  global_company_id: string | null;
  global_company_id_b: string | null;
  evidence_ref: {
    source_id?: string;
    pair_id?: string;
    final_review_required?: string;
  };
  status: string;
  disposition: string | null;
  notes?: string | null;
  name_a?: string | null;
  domain_a?: string | null;
  cr_a?: string | null;
  name_b?: string | null;
  domain_b?: string | null;
  cr_b?: string | null;
};

export type ShortCR = {
  master_account_id: string;
  global_company_id: string | null;
  cr_number_raw: string;
  valid_cr_count: number;
  rejected_tokens: string[];
};

export type TriageRow = {
  global_company_id: string;
  candidate_type: string;
  reason: string;
  identity_state: string | null;
  status: string;
  disposition: string | null;
};

export type P3ListResponse = {
  total: number;
  page: number;
  page_size: number;
  items: P3Pair[];
};

export type ShortCRResponse = {
  total: number;
  items: ShortCR[];
};

export type TriageListResponse = {
  total: number;
  page: number;
  page_size: number;
  items: TriageRow[];
};

const auth = () => ({ headers: { "X-Tenant-Id": getTenantId() } });

export async function fetchP3Pairs(params?: {
  status?: string;
  batch?: "priority" | "remainder";
  page?: number;
  pageSize?: number;
}): Promise<P3ListResponse> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/p3", {
    params: {
      status: params?.status,
      batch: params?.batch,
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 500,
    },
    ...auth(),
  });
  return res.data;
}

export async function fetchP3Count(): Promise<{ queue_type: string; count: number }> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/p3/count", auth());
  return res.data;
}

export async function fetchShortCR(): Promise<ShortCRResponse> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/short-cr", auth());
  return res.data;
}

export async function fetchTriage(params?: {
  candidateType?: string;
  page?: number;
  pageSize?: number;
}): Promise<TriageListResponse> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/triage", {
    params: {
      candidate_type: params?.candidateType,
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 500,
    },
    ...auth(),
  });
  return res.data;
}

export async function fetchTriageCounts(): Promise<{ counts: Record<string, number> }> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/triage/counts", auth());
  return res.data;
}

export async function recordDisposition(params: {
  queueType: string;
  subjectKey: string;
  disposition: string;
  reviewer: string;
  notes?: string;
}) {
  const res = await apiClient.post(
    `/api/v1/master-data/review-queue/${params.queueType}/${encodeURIComponent(params.subjectKey)}/disposition`,
    {
      disposition: params.disposition,
      reviewer: params.reviewer,
      notes: params.notes,
    },
    auth(),
  );
  return res.data;
}

// Phase 7 sales-usability (report 97). Read-only; opens no gate.
export type SalesUsabilitySummary = {
  ready_accounts: number;
  usable_accounts: number;
  by_readiness: Record<string, { total: number; usable: number }>;
  by_blocker: Record<string, number>;
  gates: Record<string, { status: string; source: string }>;
};

export type SalesUsabilityAccount = {
  global_company_id: string;
  slug: string | null;
  name: string | null;
  domain: string | null;
  city: string | null;
  sales_readiness: string;
  review_priority: string | null;
  usable: boolean;
  blockers: string[];
};

export type SalesUsabilityPage = {
  total: number;
  page: number;
  page_size: number;
  items: SalesUsabilityAccount[];
};

export async function fetchSalesUsabilitySummary(): Promise<SalesUsabilitySummary> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/sales-usability/summary", auth());
  return res.data;
}

export async function fetchSalesUsabilityAccounts(params?: {
  usable?: boolean;
  blocker?: string;
  page?: number;
  pageSize?: number;
}): Promise<SalesUsabilityPage> {
  const res = await apiClient.get("/api/v1/master-data/review-queue/sales-usability/accounts", {
    params: {
      usable: params?.usable,
      blocker: params?.blocker || undefined,
      page: params?.page ?? 1,
      page_size: params?.pageSize ?? 100,
    },
    ...auth(),
  });
  return res.data;
}
