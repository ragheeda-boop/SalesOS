import api from "./client";

export interface AccountFunnel {
  id: string;
  company_name: string;
  seller_id: string;
  intent_score: number;
  intent_level: string;
  cohort: string;
  first_action_at: string | null;
  connection_at: string | null;
  meeting_at: string | null;
  opportunity_at: string | null;
  proposal_at: string | null;
  won_at: string | null;
  lost_at: string | null;
  signal_types: string[];
  actions_count: number;
  feedback_count: number;
  feedback_accepted: number;
  feedback_rejected: number;
  outcomes_count: number;
  sector: string;
  company_size: string;
}

export interface EffectivenessDashboard {
  summary: {
    total_accounts: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
    first_actions: number;
    connections: number;
    meetings: number;
    opportunities: number;
    proposals: number;
    won: number;
    lost: number;
    revenue: number;
  };
  rates: {
    action_rate: number;
    connection_rate: number;
    meeting_rate: number;
    opportunity_rate: number;
    proposal_rate: number;
    win_rate: number;
    revenue_per_won: number;
  };
  nba: {
    total_actions: number;
    acceptance_rate: number;
    modification_rate: number;
    rejection_rate: number;
  };
  cohorts: Record<
    string,
    {
      total: number;
      action_rate: number;
      connection_rate: number;
      meeting_rate: number;
      win_rate: number;
      revenue: number;
      lift_meeting: number;
    }
  >;
  lift: {
    elevated_total: number;
    elevated_meetings: number;
    elevated_connections: number;
    baseline_total: number;
    baseline_meetings: number;
    baseline_connections: number;
    connection_lift: { value: number | null; reason: string | null; display: string };
    meeting_lift: { value: number | null; reason: string | null; display: string };
    opportunity_lift: { value: number | null; reason: string | null; display: string };
    win_lift: { value: number | null; reason: string | null; display: string };
  };
  by_level: Record<string, { count: number; action_rate: number; meeting_rate: number; win_rate: number }>;
  by_seller: Record<string, { count: number; action_rate: number; meeting_rate: number; win_rate: number }>;
}

export const effectivenessApi = {
  async getDashboard(sellerId?: string): Promise<EffectivenessDashboard> {
    const params = sellerId ? `?seller_id=${sellerId}` : "";
    const response = await api.get(`/api/v1/effectiveness/dashboard${params}`);
    return response.data;
  },

  async upsertAccount(data: {
    company_name: string;
    seller_id: string;
    intent_score: number;
    intent_level: string;
    sector?: string;
    company_size?: string;
    signal_types?: string[];
  }): Promise<AccountFunnel> {
    const response = await api.post("/api/v1/effectiveness/accounts", data);
    return response.data;
  },

  async recordEvent(data: {
    company_name: string;
    event_type: string;
    action_id?: string;
    action_type?: string;
    deal_value?: number;
    revenue?: number;
  }): Promise<{ success: boolean }> {
    const response = await api.post("/api/v1/effectiveness/events", data);
    return response.data;
  },
};
