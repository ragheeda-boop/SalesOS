import api from "./client";

export interface SignalQualification {
  signal_id: string;
  company_name: string;
  signal_type: string;
  priority: string;
  priority_score: number;
  qualification_notes: string;
}

export interface AccountPriority {
  company_name: string;
  intent_level: string;
  intent_score: number;
  signal_count: number;
  critical_signals: number;
  high_signals: number;
  recommended_action: string;
  action_urgency: string;
  metadata: Record<string, unknown>;
}

export interface NextBestAction {
  id: string;
  company_name: string;
  action_type: string;
  urgency: string;
  title: string;
  description: string;
  rationale: string;
  confidence: number;
  expires_at: string;
  signals_used: string[];
  metadata: Record<string, unknown>;
}

export interface SalesAction {
  id: string;
  nba_id: string;
  company_name: string;
  action_type: string;
  status: string;
  outcome: string;
  notes: string;
  created_at: string;
  completed_at: string | null;
  metadata: Record<string, unknown>;
}

export interface DashboardMetrics {
  total_signals: number;
  qualified_signals: number;
  total_accounts: number;
  active_actions: number;
  completed_actions: number;
  by_priority: Record<string, number>;
  by_urgency: Record<string, number>;
  by_action_type: Record<string, number>;
}

export interface QualifyRequest {
  signal_id: string;
  company_name: string;
  signal_type: string;
  raw_confidence: string;
  detected_at?: string;
  source_urls?: string[];
  source_count?: number;
}

export interface ScoreRequest {
  company_name: string;
  crm_data?: Record<string, unknown>;
}

export interface ExecuteRequest {
  nba_id: string;
  company_name: string;
  user_id: string;
}

export async function qualifySignal(data: QualifyRequest, tenantId?: string): Promise<SignalQualification> {
  const response = await api.post("/api/v1/signal-actions/qualify", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function qualifyBatch(data: QualifyRequest[], tenantId?: string): Promise<SignalQualification[]> {
  const response = await api.post("/api/v1/signal-actions/qualify-batch", { signals: data }, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function scoreAccount(data: ScoreRequest, tenantId?: string): Promise<{ priority: AccountPriority; nba: NextBestAction }> {
  const response = await api.post("/api/v1/signal-actions/score", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function executeAction(data: ExecuteRequest, tenantId?: string): Promise<SalesAction> {
  const response = await api.post("/api/v1/signal-actions/execute", data, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function completeAction(
  actionId: string,
  data: { outcome: string; notes?: string },
  tenantId?: string
): Promise<SalesAction> {
  const response = await api.post("/api/v1/signal-actions/complete", { ...data, action_id: actionId }, {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function listActions(params?: { status?: string; company_name?: string }, tenantId?: string): Promise<SalesAction[]> {
  const response = await api.get("/api/v1/signal-actions/actions", {
    params,
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}

export async function getDashboard(tenantId?: string): Promise<DashboardMetrics> {
  const response = await api.get("/api/v1/signal-actions/dashboard", {
    headers: tenantId ? { "X-Tenant-Id": tenantId } : undefined,
  });
  return response.data;
}
