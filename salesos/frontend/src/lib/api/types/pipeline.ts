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

export interface PipelineAnalyticsOpportunity {
  opportunity_id: string;
  name: string;
  stage: string;
  value: number;
  health: "healthy" | "at_risk" | "critical" | "unknown";
  health_score: number | null;
  owner: string;
}

export interface PipelineForecastSummary {
  currency: string | null;
  best_case: number | null;
  commit: number | null;
  pipeline: number | null;
  gap: number | null;
  avg_probability: number;
  total_deals: number;
  by_currency: Array<{
    currency: string;
    best_case: number;
    commit: number;
    pipeline: number;
    gap: number;
    avg_probability: number;
    total_deals: number;
  }>;
}

export interface PipelineAnalyticsSummary {
  velocity: Record<string, { avg_days: number; entries: number }>;
  conversion_rates: Record<string, number>;
  health_map: {
    healthy: number;
    at_risk: number;
    critical: number;
    unknown: number;
    opportunities: PipelineAnalyticsOpportunity[];
  };
  forecast: PipelineForecastSummary;
  total_open_deals: number;
}

export interface OpportunityNBA {
  id: string;
  opportunity_id: string;
  action: string;
  reason: string;
  confidence: number;
  confidence_label: string;
  source: string;
  alternatives: { action: string; reason: string; confidence: number }[];
  evidence: { type: string; description: string; source: string; confidence: number }[];
  potential_risks: { type: string; level: string; description: string }[];
  status: string;
  created_at: string;
  updated_at: string;
}

export interface DealIntelligence {
  deal_id: string;
  deal_name: string;
  health_score: number | null;
  health_level: "healthy" | "at_risk" | "critical" | "unknown";
  risk_factors: string[];
  opportunity_factors: string[];
  stage: string;
  value: number;
  probability: number | null;
  days_in_stage: number | null;
  activity_count: number;
  missing_fields: string[];
  generated_at: string;
  method: "deterministic_crm_rules";
}

export interface SalesRecommendation {
  id: string;
  title: string;
  description: string;
  reasoning: string;
  priority: "critical" | "high" | "medium" | "low";
  confidence: number;
  target_id: string;
  target_type: "company" | "opportunity" | "proposal" | "forecast";
  evidence: {
    source_domain: string;
    source_type: string;
    description: string;
    confidence: number;
  }[];
}

export interface RecommendationsResponse {
  items: SalesRecommendation[];
  total: number;
  source_opportunities: number;
  skipped_missing_probability: number;
  generated_at: string;
  method: "deterministic_crm_rules";
  mutated_crm: false;
}

/** POST /api/v1/pipelines — body-less; stages are stage names, not a count. */
export interface CreatePipelineResponse {
  id: string;
  name: string;
  stages: string[];
}

export interface RevenueKPI {
  total_booked: number | null;
  total_pipeline: number | null;
  weighted_pipeline: number | null;
  forecast: number | null;
  growth_percent: number | null;
  currency_consistent: boolean;
  by_currency: {
    currency: string;
    total_booked: number;
    total_pipeline: number;
    weighted_pipeline: number;
    forecast: number;
    growth_percent: number;
  }[];
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
  total_value: number | null;
  won_deals: number;
  lost_deals: number;
  win_rate: number;
  avg_deal_size: number | null;
  by_currency: {
    currency: string;
    total_deals: number;
    total_value: number;
    won_deals: number;
    lost_deals: number;
    avg_deal_size: number;
  }[];
  by_stage: { stage: string; currency: string; cnt: number; val: number }[];
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
