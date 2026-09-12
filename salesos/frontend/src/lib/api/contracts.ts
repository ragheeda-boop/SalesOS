import api from "./client";

export interface ContractParty {
  name: string;
  role: string;
  contact_email?: string;
  signatory_name?: string;
}

export interface ContractObligation {
  description: string;
  owner?: string;
  due_date?: string;
  status: string;
  completed_at?: string;
}

export interface RenewalRule {
  auto_renew: boolean;
  notice_days: number;
  renewal_term_months: number;
  max_renewals: number;
}

export interface Contract {
  id: string;
  tenant_id: string;
  opportunity_id: string;
  quote_id?: string;
  quote_revision?: number;
  title: string;
  status: string;
  parties: ContractParty[];
  obligations: ContractObligation[];
  effective_date?: string;
  expiry_date?: string;
  renewal: RenewalRule;
  legal_terms?: string;
  governing_law?: string;
  signed_by_provider?: string;
  signed_by_customer?: string;
  notes?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ContractStats {
  total: number;
  active: number;
  expiring_soon: number;
  completed: number;
  terminated: number;
}

export interface ContractListResponse {
  items: Contract[];
  total: number;
}

export async function listContracts(
  params?: { status?: string; opportunity_id?: string; page?: number; page_size?: number },
  tenantId?: string
): Promise<ContractListResponse> {
  const response = await api.get("/api/v1/contracts", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getContract(contractId: string, tenantId?: string): Promise<Contract> {
  const response = await api.get(`/api/v1/contracts/${contractId}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

/**
 * POST /api/v1/contracts — JSON body. `opportunity_id` required;
 * `quote_id` and `title` optional (FastAPI ContractCreateBody).
 */
export async function createContract(
  data: { opportunity_id: string; quote_id?: string; title?: string },
  tenantId?: string
): Promise<Contract> {
  const response = await api.post("/api/v1/contracts", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function signContract(
  contractId: string,
  data: { signed_by: string; signed_by_name: string },
  tenantId?: string
): Promise<Contract> {
  const response = await api.post(`/api/v1/contracts/${contractId}/sign`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function completeContract(contractId: string, tenantId?: string): Promise<Contract> {
  const response = await api.post(`/api/v1/contracts/${contractId}/complete`, undefined, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function terminateContract(
  contractId: string,
  data?: { reason?: string },
  tenantId?: string
): Promise<Contract> {
  const response = await api.post(`/api/v1/contracts/${contractId}/terminate`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function renewContract(
  contractId: string,
  data?: { new_expiry_date?: string },
  tenantId?: string
): Promise<Contract> {
  const response = await api.post(`/api/v1/contracts/${contractId}/renew`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getContractStats(tenantId?: string): Promise<ContractStats> {
  const response = await api.get("/api/v1/contracts/stats", {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}
