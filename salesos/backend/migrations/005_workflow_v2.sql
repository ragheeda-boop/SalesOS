-- Migration 005: Workflow Domain v2 — timeout, webhooks, jobs, job executions

ALTER TABLE workflow_definitions ADD COLUMN IF NOT EXISTS timeout_seconds DOUBLE PRECISION;

-- Webhook endpoints table
CREATE TABLE IF NOT EXISTS webhook_endpoints (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    url VARCHAR(1024) NOT NULL,
    name VARCHAR(255) NOT NULL DEFAULT '',
    auth_type VARCHAR(20) NOT NULL DEFAULT 'none',
    auth_config JSONB NOT NULL DEFAULT '{}'::jsonb,
    secret VARCHAR(512) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_tenant_id ON webhook_endpoints(tenant_id);
CREATE INDEX IF NOT EXISTS idx_webhook_endpoints_status ON webhook_endpoints(status);

-- Scheduled jobs table
CREATE TABLE IF NOT EXISTS scheduled_jobs (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    job_type VARCHAR(20) NOT NULL,
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL DEFAULT '{}'::jsonb,
    schedule VARCHAR(255) NOT NULL DEFAULT '',
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    last_run_at TIMESTAMPTZ,
    next_run_at TIMESTAMPTZ,
    run_count INTEGER NOT NULL DEFAULT 0,
    max_retries INTEGER NOT NULL DEFAULT 3,
    retry_count INTEGER NOT NULL DEFAULT 0,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_tenant_id ON scheduled_jobs(tenant_id);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_status ON scheduled_jobs(status);
CREATE INDEX IF NOT EXISTS idx_scheduled_jobs_next_run_at ON scheduled_jobs(next_run_at);

-- Job executions table
CREATE TABLE IF NOT EXISTS job_executions (
    id VARCHAR(64) PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    tenant_id VARCHAR(64) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    result JSONB,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_job_executions_job_id ON job_executions(job_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_tenant_id ON job_executions(tenant_id);
CREATE INDEX IF NOT EXISTS idx_job_executions_status ON job_executions(status);
