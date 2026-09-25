import api from "./client";

export interface ApprovalDecision {
  decision: string;
  decided_by: string;
  decided_at: string;
  comments?: string;
  authority_level: string;
}

export interface ApprovalRequest {
  id: string;
  tenant_id: string;
  target_type: string;
  target_id: string;
  requested_by: string;
  action_summary: string;
  action_evidence: string[];
  required_level: string;
  status: string;
  assigned_to?: string;
  decisions: ApprovalDecision[];
  metadata: Record<string, unknown>;
  priority: number;
  expires_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ApprovalKPIs {
  pending: number;
  approved: number;
  rejected: number;
  escalated: number;
  expired: number;
  cancelled: number;
  total: number;
}

export interface ApprovalListResponse {
  items: ApprovalRequest[];
  total: number;
}

export async function listApprovals(
  params?: { status?: string; target_type?: string; assigned_to?: string; page?: number; page_size?: number },
  tenantId?: string
): Promise<ApprovalListResponse> {
  const response = await api.get("/api/v1/approvals", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function listPendingApprovals(
  params?: { assigned_to?: string; page?: number; page_size?: number },
  tenantId?: string
): Promise<ApprovalListResponse> {
  const response = await api.get("/api/v1/approvals/pending", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getApproval(approvalId: string, tenantId?: string): Promise<ApprovalRequest> {
  const response = await api.get(`/api/v1/approvals/${approvalId}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function createApproval(
  data: {
    target_type: string;
    target_id: string;
    action_summary: string;
    action_evidence?: string[];
    required_level: string;
    assigned_to?: string;
    priority?: number;
    expires_at?: string;
  },
  tenantId?: string
): Promise<ApprovalRequest> {
  const response = await api.post("/api/v1/approvals", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function decideApproval(
  approvalId: string,
  data: { decision: string; decided_by: string; comments?: string; authority_level: string },
  tenantId?: string
): Promise<ApprovalRequest> {
  const response = await api.post(`/api/v1/approvals/${approvalId}/decide`, data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getApprovalKPIs(tenantId?: string): Promise<ApprovalKPIs> {
  const response = await api.get("/api/v1/approvals/kpis", {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}
