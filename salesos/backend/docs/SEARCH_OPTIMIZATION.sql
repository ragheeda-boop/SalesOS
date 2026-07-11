-- ============================================================================
-- SalesOS Search Performance Optimization
-- 
-- Dashboard target: POST /search p99 < 500ms
-- Current baseline: p50=180ms, p99=900ms (almost 2x budget)
--
-- This migration addresses:
--   1. Missing GIN trigram indexes for ILIKE on name_ar/name_en
--   2. Missing composite indexes for filtered search (status, city, region)
--   3. Missing partial indexes for common filter combinations
--   4. Statement timeout hardening
-- ============================================================================

BEGIN;

-- ── 1. GIN Trigram Indexes for Fuzzy Text Search ──────────────────────────
-- The full-text search uses both tsv @@ plainto_tsquery AND ILIKE on
-- name_ar/name_en. Without trigram indexes, ILIKE falls back to full
-- sequential scan. pg_trgm enables fast prefix/substring matching.

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_name_ar_gin_trgm
    ON companies USING gin (name_ar gin_trgm_ops)
    WHERE name_ar IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_name_en_gin_trgm
    ON companies USING gin (name_en gin_trgm_ops)
    WHERE name_en IS NOT NULL;

COMMENT ON INDEX ix_companies_name_ar_gin_trgm
    IS 'GIN trigram index on name_ar for fast ILIKE/prefix searches';
COMMENT ON INDEX ix_companies_name_en_gin_trgm
    IS 'GIN trigram index on name_en for fast ILIKE/prefix searches';


-- ── 2. Exact-Lookup Index on cr_number ────────────────────────────────────
-- cr_number is used for exact-match boost (CASE WHEN c.cr_number = :q THEN 8).
-- A btree index already exists (nullable=False), but make it explicit with
-- a covering index for the most common query fields to enable index-only scans.

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_cr_number_covering
    ON companies (tenant_id, cr_number)
    INCLUDE (name_ar, name_en, city, status, industry)
    WHERE cr_number IS NOT NULL;

COMMENT ON INDEX ix_companies_cr_number_covering
    IS 'Covering index on tenant_id + cr_number for exact CR lookup + common display fields';


-- ── 3. Composite Index for Filtered Search ────────────────────────────────
-- The most common filter combination is (tenant_id, city, region, status)
-- used in dashboard and company workspace search. A single composite index
-- covers all 4 fields in the WHERE clause, which is far more efficient than
-- separate single-column indexes (PostgreSQL can only use 1 index per table
-- in bitmap scans, and a composite index is always better when the leading
-- columns are used).

CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_filter_search
    ON companies (tenant_id, status, city, region)
    WHERE status IS NOT NULL OR city IS NOT NULL OR region IS NOT NULL;

COMMENT ON INDEX ix_companies_filter_search
    IS 'Composite index for common (tenant_id + status + city + region) filtered searches';


-- ── 4. Partial Indexes for Common Filter Combinations ─────────────────────
-- These partial indexes cover the most frequent filter patterns seen in
-- production. Each partial index is smaller than the full-table index,
-- making it faster to scan.

-- Active companies in a specific city (most common dashboard filter)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_active_city
    ON companies (tenant_id, city)
    WHERE status = 'active' AND city IS NOT NULL;

-- Companies in a specific industry (common for market intelligence)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_active_industry
    ON companies (tenant_id, industry)
    WHERE status = 'active' AND industry IS NOT NULL;

-- Recently updated companies (common for "recent changes" queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_recently_updated
    ON companies (tenant_id, updated_at DESC)
    WHERE status = 'active';

-- Inactive/suspended companies (compliance & audit queries)
CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_companies_inactive
    ON companies (tenant_id, updated_at DESC)
    WHERE status IN ('inactive', 'suspended', 'expired');

COMMENT ON INDEX ix_companies_active_city
    IS 'Partial index: active companies by city for dashboard search';
COMMENT ON INDEX ix_companies_active_industry
    IS 'Partial index: active companies by industry for market intelligence';
COMMENT ON INDEX ix_companies_recently_updated
    IS 'Partial index: recently updated active companies for recency sorting';
COMMENT ON INDEX ix_companies_inactive
    IS 'Partial index: inactive/suspended companies for compliance queries';


-- ── 5. Harden Statement Timeout ───────────────────────────────────────────
-- The runtime sets statement_timeout per-session, but this ensures the
-- database enforces a hard upper bound at the user/role level as a safety net.

ALTER ROLE CURRENT_USER SET statement_timeout = '5s';


-- ── 6. Refresh Full-Text Statistics ───────────────────────────────────────
-- After adding indexes, ANALYZE to update the query planner statistics.
-- Without this, PostgreSQL may not use the new indexes immediately.

ANALYZE companies;


COMMIT;
