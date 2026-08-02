/** STORY-08-06 Hub HTTP types for Studio FE. Not Production GO. */

export interface HubConnectionCreate {
  connector_key: string;
  name: string;
  credential_ref: string;
  connection_config?: Record<string, unknown>;
}

export interface HubConnection {
  id: string;
  tenant_id: string;
  connector_key: string;
  name: string;
  credential_ref: string;
  connection_config: Record<string, unknown>;
  cursor_state: Record<string, unknown>;
  is_active: boolean;
  created_at?: string | null;
  updated_at?: string | null;
}

export interface HubConnectionTestResult {
  ok: boolean;
  message: string;
  latency_ms: number;
}

export interface HubMappingCreate {
  model: string;
  mappings: Record<string, unknown>[];
  baseline_fields?: string[] | null;
  version?: number;
}

export interface HubMapping {
  id: string;
  connection_id: string;
  model: string;
  version: number;
  mappings: Record<string, unknown>[];
  baseline_fields: string[];
  is_active: boolean;
}

export interface HubConflictRule {
  internal: string;
  winner: "source" | "salesos";
  exclude_from_pull?: boolean;
}

export interface HubConflictPolicyUpsert {
  rules: HubConflictRule[];
  salesos_authored_fields?: string[] | null;
  operational_fields?: string[] | null;
}

export interface HubConflictPolicy {
  id: string;
  connection_id: string;
  rules: HubConflictRule[];
  salesos_authored_fields: string[];
  operational_fields: string[];
}

export interface HubScheduleCreate {
  model: string;
  schedule?: string;
  job_type?: "cron" | "interval" | "one_time";
  name?: string | null;
}

export interface HubScheduleResult {
  job_id: string;
  connection_id: string;
  model: string;
  schedule: string;
  job_type: string;
  next_run_at?: string | null;
}

export interface HubSyncRun {
  id: string;
  connection_id: string;
  model: string;
  status: string;
  failure_class?: string | null;
  records_pulled: number;
  records_written: number;
  records_failed: number;
  scheduled_job_id?: string | null;
  started_at: string;
  finished_at?: string | null;
  /** Tip STORY-09-09 SyncRunResponse cursor watermarks. */
  cursor_before?: Record<string, unknown>;
  cursor_after?: Record<string, unknown>;
}

export interface HubDisconnectResult {
  id: string;
  is_active: boolean;
  message: string;
}

/** Tip STORY-09-08 UnlinkedBadgeItemResponse (from SyncRun.error_log). */
export interface HubUnlinkedBadgeItem {
  kind: "unlinked_badge";
  external_id: string;
  status: "unlinked" | "invalid_cr";
  cr_number?: string | null;
  message?: string;
  model?: string;
  sync_run_id?: string | null;
  recorded_at?: string | null;
}

export interface HubUnlinkedBadgeList {
  connection_id: string;
  count: number;
  items: HubUnlinkedBadgeItem[];
}
