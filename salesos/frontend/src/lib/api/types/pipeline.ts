export interface Opportunity {
  id: string;
  name: string;
  stage: string;
  value: number;
  company_id: string;
  company_name?: string;
  currency?: string;
  probability?: number;
  health?: string;
  expected_close_date?: string;
  owner_id?: string;
  status?: string;
  description?: string;
  won_amount?: number;
  loss_reason?: string;
  created_at?: string;
  updated_at?: string;
}

export interface OpportunityListResponse {
  items: Opportunity[];
  total: number;
}

export interface Pipeline {
  id: string;
  name: string;
  stages: number;
}

export interface PipelineListResponse {
  items: Pipeline[];
}

export interface RevenueKPI {
  total_booked: number;
  total_pipeline: number;
  weighted_pipeline: number;
  forecast: number;
  growth_percent: number;
}

export interface TeamKPI {
  total_employees: number;
  active_employees: number;
  top_performers: Record<string, unknown>[];
  avg_win_rate: number;
}

export interface RiskKPI {
  expiring_contracts: number;
  stalled_deals: number;
  inactive_companies: number;
  low_pipeline_employees: number;
}

export interface PipelineHealth {
  total_deals: number;
  total_value: number;
  won_deals: number;
  lost_deals: number;
  win_rate: number;
  avg_deal_size: number;
  by_stage: { stage: string; cnt: number; val: number }[];
}

export interface RenewalKPI {
  due_next_30_days: number;
  due_next_90_days: number;
  total_renewal_value: number;
  at_risk: Record<string, unknown>[];
}

export interface GrowthKPI {
  new_companies_30d: number;
  new_contacts_30d: number;
  new_opportunities_30d: number;
  new_contracts_30d: number;
}

export interface HealthKPI {
  overall_health: string;
  data_completeness: number;
  sync_status: string;
  last_activity: string;
}

export interface ExecutiveDashboardResponse {
  revenue: RevenueKPI;
  team: TeamKPI;
  risk: RiskKPI;
  health: HealthKPI;
  pipeline: PipelineHealth;
  renewals: RenewalKPI;
  growth: GrowthKPI;
}
