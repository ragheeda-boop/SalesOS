/** STORY-08-06 Hub HTTP types for STORY-08-07 Studio. Not Production GO. */

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
}

export interface HubDisconnectResult {
  id: string;
  is_active: boolean;
  message: string;
}
