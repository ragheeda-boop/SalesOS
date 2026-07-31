export interface ActivityRecord {
  id: string;
  tenant_id: string;
  actor: string;
  action: string;
  entity_type: string;
  entity_id: string;
  target_type?: string;
  target_id?: string;
  metadata?: Record<string, unknown>;
  timestamp: string;
}

export interface EntityActivityResponse {
  entity_type: string;
  entity_id: string;
  items: ActivityRecord[];
  total: number;
}

export interface ActivityQueryResponse {
  items: ActivityRecord[];
  total: number;
  limit: number;
  offset: number;
}

export interface ActivityDashboardDTO {
  email_count: number;
  meeting_count: number;
  followup_count: number;
  overdue_count: number;
  top_companies: Array<{ company_id: string; name: string; count: number }>;
  engagement_trend: Array<{ date: string; value: number }>;
}

export interface CompanyEngagementDTO {
  company_id: string;
  email_count: number;
  meeting_count: number;
  last_activity: string | null;
  last_email: string | null;
  last_meeting: string | null;
  followup_status: string;
  score?: EngagementScoreDTO;
}

export interface EngagementScoreDTO {
  company_id: string;
  email_count_sent: number;
  email_count_received: number;
  reply_rate: number;
  meeting_count: number;
  meeting_hours: number;
  meeting_completion_rate: number;
  last_email_days: number | null;
  last_meeting_days: number | null;
  last_activity_days: number | null;
  communication_velocity: number;
  response_time_avg_hours: number | null;
  followup_delay_days: number | null;
  relationship_health: number;
}

export interface FollowUpStatusDTO {
  company_id: string;
  assigned: boolean;
  need_followup: boolean;
  waiting_customer: boolean;
  waiting_you: boolean;
  overdue: boolean;
  last_outbound_days: number | null;
  priority: "low" | "medium" | "high" | "critical";
}

export interface FollowupDashboardDTO {
  total: number;
  overdue: number;
  need_followup: number;
  waiting_you: number;
  waiting_customer: number;
  items: FollowUpStatusDTO[];
}

export interface EmailMetricsDTO {
  total_sent: number;
  total_received: number;
  reply_rate: number;
  avg_response_hours: number | null;
  top_companies: Array<{ company_id: string; count: number }>;
}

export interface CalendarMetricsDTO {
  total_events: number;
  total_hours: number;
  meeting_count: number;
  avg_duration_minutes: number;
  upcoming: Array<{
    title: string;
    start_time: string;
    company_id: string | null;
  }>;
}

export interface EngagementSummaryDTO {
  total_companies: number;
  active_companies: number;
  avg_relationship_health: number;
  stagnant_companies: number;
  top_engaged: Array<{ company_id: string; name: string; health: number }>;
}
