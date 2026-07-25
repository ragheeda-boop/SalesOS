-- 006_database_indexes.sql
-- Adds missing composite indexes, FK indexes, and pg_trgm extension for performance.
-- Reversible: each CREATE has a corresponding DROP.

BEGIN;

-- Enable trigram extension for ILIKE '%query%' searches
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ============================================================
-- Company: composite indexes for tenant-scoped queries
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_companies_tenant_confidence ON companies (tenant_id, confidence_score);
CREATE INDEX IF NOT EXISTS ix_companies_tenant_golden ON companies (tenant_id, is_golden_record);
CREATE INDEX IF NOT EXISTS ix_companies_tenant_created ON companies (tenant_id, created_at);
CREATE INDEX IF NOT EXISTS ix_companies_tenant_status ON companies (tenant_id, status);

-- License: composite index for expiry queries
CREATE INDEX IF NOT EXISTS ix_licenses_expiry_status ON licenses (expiry_date, status);

-- ============================================================
-- Golden Records: FK index + composite indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_golden_records_tenant_company ON golden_records (tenant_id, company_id);
CREATE INDEX IF NOT EXISTS ix_golden_records_tenant_active ON golden_records (tenant_id, is_active);

-- ============================================================
-- Entity Resolution Conflicts: composite + status index
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_conflicts_tenant_status ON entity_resolution_conflicts (tenant_id, status);

-- ============================================================
-- Timeline: entity lookup + tenant-scoped time range
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_timeline_entity ON timeline_entries (entity_type, entity_id);
CREATE INDEX IF NOT EXISTS ix_timeline_tenant_created ON timeline_entries (tenant_id, created_at);
CREATE INDEX IF NOT EXISTS ix_timeline_event_type ON timeline_entries (event_type);

-- ============================================================
-- Identity: device sessions + token blacklist cleanup
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_device_sessions_tenant ON device_sessions (tenant_id);
CREATE INDEX IF NOT EXISTS ix_device_sessions_expires ON device_sessions (expires_at);
CREATE INDEX IF NOT EXISTS ix_token_blacklist_expires ON token_blacklist (expires_at);

-- ============================================================
-- Admin: composite indexes for billing/license queries
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_admin_licenses_tenant_active ON admin_licenses (tenant_id, is_active);
CREATE INDEX IF NOT EXISTS ix_admin_invoices_tenant_status ON admin_invoices (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_admin_invoices_due ON admin_invoices (due_date);
CREATE INDEX IF NOT EXISTS ix_admin_transactions_tenant_status ON admin_transactions (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_admin_ai_costs_tenant_model ON admin_ai_costs (tenant_id, model);
CREATE INDEX IF NOT EXISTS ix_admin_health_ts ON admin_health_snapshots (timestamp);

-- ============================================================
-- Revenue Execution: composite indexes
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_opportunities_tenant_stage ON opportunities (tenant_id, stage);
CREATE INDEX IF NOT EXISTS ix_opportunities_company ON opportunities (company_id);
CREATE INDEX IF NOT EXISTS ix_tasks_tenant_priority ON tasks (tenant_id, priority);
CREATE INDEX IF NOT EXISTS ix_tasks_assignee_completed ON tasks (assignee_id, completed);

-- ============================================================
-- Notifications: composite indexes for user inbox + tenant type
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_notifications_user_read ON notifications (user_id, read, created_at);
CREATE INDEX IF NOT EXISTS ix_notifications_tenant_type ON notifications (tenant_id, type);

-- ============================================================
-- Scoring: composite index for target lookups
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_scorecards_tenant_target ON scoring_scorecards (tenant_id, target_id, generated_at);

-- ============================================================
-- Commercial: composite indexes for opportunity/quote/contract/meeting queries
-- ============================================================
CREATE INDEX IF NOT EXISTS ix_commercial_opps_tenant_stage ON commercial_opportunities (tenant_id, stage);
CREATE INDEX IF NOT EXISTS ix_commercial_opps_tenant_status ON commercial_opportunities (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_commercial_opps_owner ON commercial_opportunities (owner_id);

CREATE INDEX IF NOT EXISTS ix_stage_entries_opportunity ON commercial_stage_entries (opportunity_id);
CREATE INDEX IF NOT EXISTS ix_stage_entries_tenant_entered ON commercial_stage_entries (tenant_id, entered_at);

CREATE INDEX IF NOT EXISTS ix_activity_sessions_tenant_status ON commercial_activity_sessions (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_activity_sessions_target ON commercial_activity_sessions (target_id, target_type);

CREATE INDEX IF NOT EXISTS ix_activities_type_status ON commercial_activities (activity_type, status);
CREATE INDEX IF NOT EXISTS ix_activities_owner ON commercial_activities (owner_id);

CREATE INDEX IF NOT EXISTS ix_commercial_quotes_tenant_status ON commercial_quotes (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_commercial_proposals_tenant_status ON commercial_proposals (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_commercial_contracts_tenant_status ON commercial_contracts (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_commercial_contracts_expiry ON commercial_contracts (expiry_date);

CREATE INDEX IF NOT EXISTS ix_meetings_tenant_date ON meetings (tenant_id, meeting_date);
CREATE INDEX IF NOT EXISTS ix_meetings_status ON meetings (status);
CREATE INDEX IF NOT EXISTS ix_emails_tenant_sent ON emails (tenant_id, sent_at);
CREATE INDEX IF NOT EXISTS ix_emails_direction ON emails (direction);

CREATE INDEX IF NOT EXISTS ix_commercial_recs_tenant_status ON commercial_recommendations (tenant_id, status);
CREATE INDEX IF NOT EXISTS ix_commercial_recs_target ON commercial_recommendations (target_id, target_type);

-- ============================================================
-- Feature Store: index on entity lookups (already in ORM, ensuring DDL)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_feature_values_entity_computed ON feature_values (entity_type, entity_id, computed_at);

COMMIT;
