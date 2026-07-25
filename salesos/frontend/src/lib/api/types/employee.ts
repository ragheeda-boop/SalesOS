import type { CursorResponse } from"./common";

export { CursorResponse };

export interface EmployeeProfile {
  id: string;
  full_name: string;
  full_name_ar: string | null;
  email: string;
  role: string;
  department: string | null;
  phone: string | null;
  avatar_url: string | null;
  is_active: boolean;
  tenant_id: string;
  created_at: string;
  team: Record<string, unknown>[];
  manager: Record<string, unknown> | null;
}

export interface EmployeePortfolio {
 companies: Record<string, unknown>[];
 contacts: Record<string, unknown>[];
 pipeline: { id: string; name: string; type: string; value: number; status: string; company_id?: string; company_name?: string }[];
 revenue: number;
 contracts: { id: string; name: string; type: string; value: number; status: string }[];
 projects: Record<string, unknown>[];
}

export interface ActivityIntelligence {
 meetings: number;
 emails: number;
 calls: number;
 tasks: number;
 notes: number;
 documents: number;
 total: number;
 recent: Record<string, unknown>[];
}

export interface CalendarIntelligence {
 today_count: number;
 week_count: number;
 month_count: number;
 total_hours: number;
 avg_duration_minutes: number;
 unique_companies_met: number;
 upcoming: Record<string, unknown>[];
}

export interface EmailIntelligence {
 sent: number;
 received: number;
 replies: number;
 avg_response_hours: number;
 top_contacts: Record<string, unknown>[];
 top_companies: Record<string, unknown>[];
}

export interface EmployeeKPIs {
 revenue: number;
 pipeline: number;
 win_rate: number;
 response_rate: number;
 follow_up_rate: number;
 activities: number;
 productivity: number;
 forecast: number;
}

export interface AICoachAction {
 type: string;
 title: string;
 description: string;
 priority: string;
 target_id?: string;
 target_type?: string;
}

export interface Employee360Response {
 profile: EmployeeProfile;
 portfolio: EmployeePortfolio;
 calendar_intelligence: CalendarIntelligence;
 email_intelligence: EmailIntelligence;
 activity_intelligence: ActivityIntelligence;
 kpis: EmployeeKPIs;
 ai_coach: AICoachAction[];
}

export interface EmployeeListItem {
 id: string;
 full_name: string;
 full_name_ar: string | null;
 email: string;
 role: string;
 department: string | null;
 phone: string | null;
 avatar_url: string | null;
 is_active: boolean;
 signal_count: number;
 score: number | null;
 score_trend:"up" |"down" |"stable" | null;
 confidence: number | null;
 created_at: string;
}

export interface EmployeeSearchParams {
 q?: string;
 department?: string;
 role?: string;
 signal_count_min?: number;
 signal_count_max?: number;
 cursor?: string;
 page_size?: number;
}

export interface SignalTypeBreakdown {
 type: string;
 count: number;
 label: string;
}

export interface SignalSourceBreakdown {
 source: string;
 count: number;
 label: string;
}

export interface SignalTrendPoint {
 date: string;
 count: number;
}

export interface EmployeeSignalsResponse {
 by_type: SignalTypeBreakdown[];
 by_source: SignalSourceBreakdown[];
 trend: SignalTrendPoint[];
 total: number;
}

export interface ScoreFactor {
 name: string;
 contribution: number;
 signal_type: string;
 label: string;
}

export interface EmployeeScoreResponse {
 score: number;
 trend:"up" |"down" |"stable";
 confidence: number;
 factors: ScoreFactor[];
}

export interface EmployeeTimelineParams {
 source?: string[];
 type?: string[];
 from?: string;
 to?: string;
 cursor?: string;
 page_size?: number;
}

export interface EmployeeTimelineEvent {
 id: string;
 action: string;
 title: string;
 source: string;
 source_label: string;
 timestamp: string;
 actor: string;
 entity_type?: string;
 entity_id?: string;
 metadata?: Record<string, unknown>;
}

export interface EmployeeTimelineResponse {
 events: EmployeeTimelineEvent[];
 next_cursor: string | null;
 has_next: boolean;
 total: number;
}

export interface ScoreTrendPoint {
 date: string;
 score: number;
}

export interface PeerComparison {
 metric: string;
 employee_value: number;
 department_avg: number;
 label: string;
}

export interface RiskFlag {
 type: string;
 label: string;
 severity:"high" |"medium" |"low";
 description: string;
}

export interface EmployeePerformanceResponse {
 score_trend: ScoreTrendPoint[];
 peer_comparison: PeerComparison[];
 risk_flags: RiskFlag[];
 factors: ScoreFactor[];
 current_score: number;
 score_trend_direction:"up" |"down" |"stable";
 department: string | null;
}

export interface BulkEditEmployeesRequest {
  ids?: string[];
  all?: boolean;
  department?: string;
  role?: string;
  status?: string;
}

export interface CalendarKPIsResponse {
  today_count: number;
  week_count: number;
  month_count: number;
  total_hours: number;
  avg_duration_minutes: number;
  cancelled_this_month: number;
  cancellation_rate: number;
  internal_count: number;
  external_count: number;
  unique_companies_met: number;
  focus_time_hours: number;
  calendar_utilization: number;
  upcoming: CalendarUpcomingEvent[];
}

export interface CalendarUpcomingEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  is_internal: boolean;
  attendees_count: number;
}

export interface CalendarHeatmapPoint {
  day: string;
  hours: Record<string, number>;
}

export interface EmailKPIsResponse {
  sent: number;
  received: number;
  total: number;
  internal: number;
  external: number;
  reply_rate: number;
  avg_response_hours: number;
  unread_count: number;
  has_attachments: number;
  sentiment_positive: number;
  sentiment_negative: number;
  period_days: number;
}

export interface TopContactItem {
  address: string;
  count: number;
}

export interface DailyVolumePoint {
  date: string;
  sent: number;
  received: number;
}

export interface ProductivityResponse {
  productivity_score: number;
  activity_score: number;
  focus_score: number;
  task_completion_rate: number;
  meetings_per_day: number;
  emails_per_day: number;
  meeting_hours_total: number;
  signal_count: number;
  burnout_risk: "low" | "medium" | "high";
  trend_direction: "improving" | "declining" | "stable";
  first_half_signals: number;
  second_half_signals: number;
  period_days: number;
}

export interface RelationshipScoreResponse {
  employee_id: string;
  target_id: string;
  target_type: string;
  relationship_score: number;
  strength: "strong" | "moderate" | "weak";
  meetings_last_90d: number;
  emails_last_90d: number;
  days_since_last_contact: number;
}

export interface ExecutiveSummaryResponse {
  total_employees: number;
  active_employees: number;
  new_this_month: number;
  avg_score: number;
  total_signals_30d: number;
  at_risk_count: number;
  departments: { name: string; headcount: number }[];
  roles: { role: string; count: number }[];
  top_performers: { id: string; name: string; department: string; role: string; score: number }[];
  generated_at: string;
}
