import type { PaginatedResponse } from "./common";

export { PaginatedResponse };

export interface PipelineMetrics {
  records_ingested: number;
  total_valid: number;
  total_errors: number;
  errors_by_stage: Record<string, number>;
  golden_records_created: number;
  golden_records_merged: number;
  companies_synced: number;
  embeddings_stored: number;
  kg_triples_created: number;
  features_computed: number;
  stage_durations_ms: Record<string, number>;
  total_duration_ms: number;
  last_run_at: string | null;
}

export interface FeatureStoreMetrics {
  computations: number;
  errors: number;
  cache_hits: number;
  cache_misses: number;
  total_compute_ms: number;
}

export interface FullHealthResponse {
  status: string;
  checks: Record<string, string>;
  pipeline: PipelineMetrics | { status: string };
}

export interface GoldenRecordAdmin {
  id: string;
  tenant_id: string;
  cr_number: string | null;
  company_name_ar: string | null;
  status: string;
  confidence_score: number | null;
  source_records: number;
  created_at: string;
  updated_at: string;
}

export interface EntityResolutionConflict {
  id: string;
  tenant_id: string;
  cr_number_a: string;
  cr_number_b: string;
  status: string;
  reason: string;
  created_at: string;
}

export interface DlqEntry {
  id: number;
  source_slug: string;
  cr_number: string | null;
  stage: string;
  error_message: string;
  error_type: string | null;
  retry_count: number;
  max_retries: number;
  status: string;
  created_at: string;
  last_retry_at: string | null;
}

export interface DlqRetryResponse {
  processed: number;
  retried: number;
  resolved: number;
  still_failed: number;
}

export interface TaskResponse {
  id: string;
  title: string;
  priority: string;
  source: string;
  company_id?: string | null;
  completed: boolean;
  created_at?: string | null;
}

export interface AdminTenantListItem {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  plan: string;
  is_active: boolean;
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminTenantDetail {
  id: string;
  name: string;
  slug: string;
  domain: string | null;
  plan: string;
  is_active: boolean;
  settings: Record<string, unknown>;
  features: Record<string, unknown>;
  user_count: number;
  subscription_ends_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminTenantUsage {
  tenant_id: string;
  tenant_name: string;
  api_calls: number;
  storage_mb: number;
  active_users: number;
  total_users: number;
  period_start: string;
  period_end: string;
}

export interface AdminPlan {
  id: string;
  name: string;
  tier: string;
  price_monthly: number;
  price_yearly: number;
  max_users: number;
  max_storage_mb: number;
  max_api_calls: number;
  features: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminLicense {
  id: string;
  tenant_id: string;
  tenant_name: string;
  plan_id: string;
  plan_name: string;
  tier: string;
  is_active: boolean;
  starts_at: string | null;
  ends_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminUser {
  id: string;
  email: string;
  full_name: string;
  full_name_ar: string | null;
  role: string;
  is_active: boolean;
  is_verified: boolean;
  tenant_id: string;
  tenant_name: string;
  created_at: string;
  last_login_at: string | null;
}

export interface AdminUserDetail extends AdminUser {
  permissions: string[];
  updated_at: string;
}

export interface AdminInvoice {
  id: string;
  tenant_id: string;
  tenant_name: string;
  amount: number;
  currency: string;
  status: string;
  description: string;
  due_date: string | null;
  paid_at: string | null;
  created_at: string;
}

export interface AdminTransaction {
  id: string;
  tenant_id: string;
  tenant_name: string;
  amount: number;
  currency: string;
  status: string;
  method: string;
  description: string;
  reference: string | null;
  created_at: string;
}

export interface AdminFeatureFlag {
  id: string;
  key: string;
  name: string;
  description: string | null;
  enabled: boolean;
  is_global: boolean;
  created_at: string;
  updated_at: string;
}

export interface AdminFlagTenant {
  flag_id: string;
  flag_key: string;
  tenant_id: string;
  tenant_name: string;
  enabled: boolean;
}

export interface AdminJob {
  id: string;
  type: string;
  status: string;
  progress: number;
  tenant_id: string | null;
  created_by: string | null;
  payload: Record<string, unknown>;
  result: Record<string, unknown> | null;
  error_message: string | null;
  retry_count: number;
  max_retries: number;
  scheduled_at: string | null;
  started_at: string | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
}

export interface AdminJobDetail extends AdminJob {
  logs: { level: string; message: string; timestamp: string }[];
}

export interface AdminAICost {
  id: string;
  model: string;
  tenant_id: string | null;
  tenant_name: string | null;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  operation: string;
  created_at: string;
}

export interface AdminAICostSummary {
  total_cost: number;
  total_tokens: number;
  by_model: { model: string; cost: number; tokens: number }[];
  by_tenant: { tenant_id: string; cost: number; tokens: number }[];
  by_operation: { operation: string; cost: number; tokens: number }[];
}

export interface AdminAIUsage {
  total_prompt_tokens: number;
  total_completion_tokens: number;
  total_tokens: number;
  by_model: {
    model: string;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  }[];
  by_tenant: {
    tenant_id: string;
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  }[];
}

export interface AdminHealthComponent {
  component: string;
  status: string;
  latency_ms: number | null;
  last_check: string | null;
  details: string | null;
}

export interface AdminDetailedHealth {
  overall_status: string;
  uptime_seconds: number;
  components: AdminHealthComponent[];
}

export interface AdminHealthHistoryEntry {
  timestamp: string;
  overall_status: string;
  components: Record<string, string>;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  action_type: string;
  actor_id: string;
  actor_name: string;
  actor_email: string;
  resource: string;
  resource_type: string;
  resource_id: string;
  tenant_id: string | null;
  tenant_name: string | null;
  details: Record<string, unknown> | null;
  ip_address: string | null;
  user_agent: string | null;
  created_at: string;
}

export interface AdminPermission {
  id: string;
  key: string;
  name: string;
  description: string | null;
  group: string;
}

export interface AdminRole {
  id: string;
  name: string;
  description: string | null;
  permissions: string[];
  is_system: boolean;
  user_count: number;
  created_at: string;
  updated_at: string;
}

export interface AdminConfigVersion {
  version: number;
  content: string;
  created_at: string;
  created_by: string;
}

export interface AdminConfigResponse {
  content: string;
  version: number;
  versions: AdminConfigVersion[];
}

export interface CopilotFeedbackRequest {
  message_id: string;
  rating: "positive" | "negative";
  comment?: string;
}

export interface CopilotFeedbackResponse {
  success: boolean;
  helpful_rate?: number;
  total_ratings?: number;
}

export interface CopilotTelemetrySummary {
  total_calls: number;
  success_rate: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
}

export interface CopilotToolTelemetry {
  tool_name: string;
  total_calls: number;
  success_count: number;
  failure_count: number;
  success_rate: number;
  latency_p50_ms: number;
  latency_p95_ms: number;
  latency_p99_ms: number;
  avg_result_count: number;
}

export interface CopilotLatencyBucket {
  label: string;
  p50: number;
  p95: number;
  p99: number;
}

export interface CopilotResultBucket {
  label: string;
  count: number;
}

export interface CopilotVolumePoint {
  date: string;
  calls: number;
  successes: number;
  failures: number;
}

export interface CopilotTelemetryData {
  summary: CopilotTelemetrySummary;
  tools: CopilotToolTelemetry[];
  latency_distribution: CopilotLatencyBucket[];
  result_histogram: CopilotResultBucket[];
  volume_over_time: CopilotVolumePoint[];
}
