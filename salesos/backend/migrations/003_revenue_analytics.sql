-- Migration 003: Revenue Analytics Snapshots
CREATE TABLE IF NOT EXISTS revenue_analytics_snapshots (
    id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    period_start TIMESTAMPTZ,
    period_end TIMESTAMPTZ,
    values JSONB NOT NULL DEFAULT '[]'::jsonb,
    generated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    version INTEGER NOT NULL DEFAULT 1
);
CREATE INDEX idx_revenue_analytics_tenant_id ON revenue_analytics_snapshots(tenant_id);
