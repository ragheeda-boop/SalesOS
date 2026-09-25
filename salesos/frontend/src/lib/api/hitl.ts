import api from "./client";

export interface NbaFeedback {
  id: string;
  tenant_id: string;
  company_name: string;
  action_id: string;
  recommendation_id: string;
  seller_id: string;
  decision: "accepted" | "rejected" | "modified";
  reason_code: string;
  notes: string;
  original_action_type: string;
  modified_action_type: string;
  modified_target_contact_id: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface ActionOutcome {
  id: string;
  tenant_id: string;
  action_id: string;
  company_name: string;
  opportunity_id: string | null;
  seller_id: string;
  outcome_type: string;
  notes: string;
  contact_reached: string;
  duration_seconds: number | null;
  followup_required: boolean;
  occurred_at: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface SalesFollowup {
  id: string;
  tenant_id: string;
  parent_action_id: string;
  parent_outcome_id: string;
  company_name: string;
  seller_id: string;
  generated_action_type: string;
  title: string;
  description: string;
  due_at: string;
  rationale: string;
  status: string;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface WorkQueue {
  pending_actions: Array<{
    id: string;
    company_name: string;
    action_type: string;
    status: string;
    notes: string;
    created_at: string;
  }>;
  pending_followups: SalesFollowup[];
  recent_outcomes: Array<{
    id: string;
    company_name: string;
    outcome_type: string;
    notes: string;
    occurred_at: string;
  }>;
  summary: {
    pending_actions: number;
    pending_followups: number;
    outcomes_7d: number;
    connected_7d: number;
  };
}

export interface FeedbackMetrics {
  seller_id: string;
  feedback: {
    total: number;
    accepted: number;
    rejected: number;
    modified: number;
    acceptance_rate: number;
  };
  outcomes: {
    total: number;
    by_type: Record<string, number>;
    positive_outcomes: number;
    conversion_rate: number;
  };
  followups: {
    total: number;
    by_status: Record<string, number>;
    completion_rate: number;
  };
}

export async function recordFeedback(data: {
  action_id: string;
  recommendation_id: string;
  company_name: string;
  seller_id?: string;
  decision: string;
  reason_code?: string;
  notes?: string;
  original_action_type: string;
  modified_action_type?: string;
  modified_target_contact_id?: string;
}, tenantId?: string): Promise<NbaFeedback> {
  const res = await api.post("/api/v1/hitl/feedback", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function recordOutcome(data: {
  action_id: string;
  company_name: string;
  opportunity_id?: string;
  idempotency_key: string;
  seller_id?: string;
  outcome_type: string;
  notes?: string;
  contact_reached?: string;
  duration_seconds?: number;
  followup_required?: boolean;
  occurred_at?: string;
}, tenantId?: string): Promise<{ outcome: ActionOutcome; followup: SalesFollowup | null }> {
  const res = await api.post("/api/v1/hitl/outcomes", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function getMyDay(tenantId?: string): Promise<WorkQueue> {
  const res = await api.get("/api/v1/hitl/my-day", {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function listFollowups(sellerId?: string, tenantId?: string): Promise<{ count: number; followups: SalesFollowup[] }> {
  const res = await api.get("/api/v1/hitl/followups", {
    params: sellerId ? { seller_id: sellerId } : undefined,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function completeFollowup(followupId: string, outcome = "completed", tenantId?: string): Promise<void> {
  await api.post(`/api/v1/hitl/followups/${followupId}/complete`, { outcome }, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
}

export async function getFeedbackMetrics(sellerId: string, tenantId?: string): Promise<FeedbackMetrics> {
  const res = await api.get(`/api/v1/hitl/metrics/${sellerId}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function getCompanyFeedback(companyName: string, tenantId?: string): Promise<{ count: number; feedback: NbaFeedback[] }> {
  const res = await api.get(`/api/v1/hitl/feedback/company/${encodeURIComponent(companyName)}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export async function getCompanyOutcomes(companyName: string, tenantId?: string): Promise<{ count: number; outcomes: ActionOutcome[] }> {
  const res = await api.get(`/api/v1/hitl/outcomes/company/${encodeURIComponent(companyName)}`, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}

export interface FeedbackAnalytics {
  acceptance_rate: number;
  modification_rate: number;
  rejection_rate: number;
  total_feedback: number;
  total_outcomes: number;
  conversion_rate: number;
  avg_hours_to_action: number;
  tta_sample_size: number;
  seller_productivity: Array<{
    seller_id: string;
    total_outcomes: number;
    converted: number;
    conversion_rate: number;
  }>;
  decision_breakdown: Array<{
    decision: string;
    count: number;
  }>;
}

export async function getFeedbackAnalytics(sellerId?: string, tenantId?: string): Promise<FeedbackAnalytics> {
  const res = await api.get("/api/v1/hitl/analytics", {
    params: sellerId ? { seller_id: sellerId } : undefined,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return res.data;
}
