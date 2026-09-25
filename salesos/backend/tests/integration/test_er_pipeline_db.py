"""Phase 3 Integration Tests — Entity Resolution Pipeline on Real PostgreSQL.

Tests the matching pipeline, field provenance, and quality scoring
against a real, dedicated, disposable database on localhost:5432.

This suite TRUNCATEs every md_* table on setup, so it must never point at
salesos_test: that database holds the restored MUHIDE evidence and the
recorded human review decisions (md_review_queue_state,
md_person_company_link_proposals), which this truncate previously wiped.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime

import asyncpg
import pytest

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test_er_pipeline"


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB,
    )


PHASE0_DDL = """
CREATE TABLE IF NOT EXISTS md_global_companies (
    id UUID PRIMARY KEY,
    slug VARCHAR(64) NOT NULL,
    canonical_name VARCHAR(512) NOT NULL,
    canonical_name_ar VARCHAR(512),
    canonical_name_en VARCHAR(512),
    cr_number VARCHAR(50),
    vat_number VARCHAR(50),
    unified_national_number VARCHAR(50),
    domain VARCHAR(255),
    website VARCHAR(512),
    city VARCHAR(100),
    region VARCHAR(100),
    country VARCHAR(100) NOT NULL DEFAULT 'Saudi Arabia',
    industry VARCHAR(255),
    legal_entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    source_count INT NOT NULL DEFAULT 1,
    phone VARCHAR(50),
    email VARCHAR(255),
    address TEXT,
    latitude FLOAT,
    longitude FLOAT,
    metadata JSONB NOT NULL DEFAULT '{}',
    merged_from_ids JSONB,
    merged_at TIMESTAMPTZ,
    split_from_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_companies_slug ON md_global_companies (slug);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_companies_slug2 ON md_global_companies (slug) WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS md_global_people (
    id UUID PRIMARY KEY,
    slug VARCHAR(64) NOT NULL,
    canonical_name VARCHAR(512) NOT NULL,
    email VARCHAR(255),
    phone VARCHAR(50),
    company_global_id UUID,
    job_title VARCHAR(255),
    linkedin_url VARCHAR(512),
    confidence_score FLOAT NOT NULL DEFAULT 0.0,
    source_count INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'active',
    metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_people_slug ON md_global_people (slug);

CREATE TABLE IF NOT EXISTS md_legacy_id_mappings (
    id UUID PRIMARY KEY,
    legacy_id_type VARCHAR(32) NOT NULL,
    legacy_id VARCHAR(255) NOT NULL,
    global_entity_type VARCHAR(32) NOT NULL,
    global_entity_id UUID NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_legacy_id_lookup ON md_legacy_id_mappings (legacy_id_type, legacy_id);

CREATE TABLE IF NOT EXISTS md_source_files (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    filename VARCHAR(512) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL,
    file_hash_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL,
    mime_type VARCHAR(128) NOT NULL,
    sheet_count INT NOT NULL,
    total_rows INT NOT NULL,
    source_system VARCHAR(64) NOT NULL,
    schema_mapping JSONB,
    uploaded_by UUID NOT NULL,
    uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded',
    deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_md_source_files_hash ON md_source_files (file_hash_sha256);

CREATE TABLE IF NOT EXISTS md_source_rows (
    id UUID PRIMARY KEY,
    tenant_id UUID NOT NULL,
    source_file_id UUID NOT NULL,
    source_id VARCHAR(64) NOT NULL,
    source_record_id VARCHAR(255) NOT NULL,
    row_number INT NOT NULL,
    sheet_name VARCHAR(255),
    raw_payload JSONB NOT NULL,
    normalized_payload JSONB,
    entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    global_entity_id UUID,
    resolution_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resolution_confidence FLOAT,
    resolution_method VARCHAR(64),
    import_batch_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_source_rows_source ON md_source_rows (source_id, source_record_id);

CREATE TABLE IF NOT EXISTS md_entity_matches (
    id UUID PRIMARY KEY,
    global_entity_id UUID,
    source_a_id VARCHAR(255) NOT NULL,
    source_b_id VARCHAR(255) NOT NULL,
    match_score FLOAT NOT NULL DEFAULT 0.0,
    match_method VARCHAR(64) NOT NULL,
    match_signals JSONB NOT NULL DEFAULT '[]',
    match_status VARCHAR(32) NOT NULL DEFAULT 'pending_review',
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ,
    review_decision VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_entity_matches_entity ON md_entity_matches (global_entity_id);
CREATE INDEX IF NOT EXISTS ix_md_entity_matches_status ON md_entity_matches (match_status);

CREATE TABLE IF NOT EXISTS md_entity_conflicts (
    id UUID PRIMARY KEY,
    global_entity_id UUID,
    field_name VARCHAR(128) NOT NULL,
    value_a TEXT,
    source_a_id VARCHAR(255),
    source_a_priority INT DEFAULT 0,
    value_b TEXT,
    source_b_id VARCHAR(255),
    source_b_priority INT DEFAULT 0,
    is_government_id BOOLEAN NOT NULL DEFAULT false,
    veto_enabled BOOLEAN NOT NULL DEFAULT false,
    resolution VARCHAR(32) NOT NULL DEFAULT 'open',
    resolved_value TEXT,
    resolved_by UUID,
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_entity_conflicts_entity ON md_entity_conflicts (global_entity_id, resolution);

CREATE TABLE IF NOT EXISTS md_entity_merge_history (
    id UUID PRIMARY KEY,
    operation VARCHAR(32) NOT NULL,
    target_entity_id UUID NOT NULL,
    source_entity_ids JSONB NOT NULL DEFAULT '[]',
    match_score FLOAT,
    match_method VARCHAR(64),
    performed_by UUID,
    performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    rollback_available BOOLEAN NOT NULL DEFAULT true,
    rolled_back_at TIMESTAMPTZ,
    details JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_md_merge_history_entity ON md_entity_merge_history (target_entity_id);

CREATE TABLE IF NOT EXISTS md_field_provenance (
    id UUID PRIMARY KEY,
    global_entity_id UUID NOT NULL,
    field_name VARCHAR(128) NOT NULL,
    field_value TEXT NOT NULL,
    source_row_id UUID,
    source_file_id UUID,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    evidence_tier VARCHAR(64) NOT NULL,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified',
    verified_by UUID,
    verified_at TIMESTAMPTZ,
    authority_score FLOAT NOT NULL DEFAULT 0.0,
    selection_reason VARCHAR(128),
    conflict_status VARCHAR(32) NOT NULL DEFAULT 'none',
    is_current BOOLEAN NOT NULL DEFAULT true,
    superseded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_field_provenance_entity ON md_field_provenance (global_entity_id, field_name);

CREATE TABLE IF NOT EXISTS md_quality_scores (
    id UUID PRIMARY KEY,
    global_entity_id UUID NOT NULL,
    completeness_score FLOAT NOT NULL DEFAULT 0.0,
    accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    consistency_score FLOAT NOT NULL DEFAULT 0.0,
    freshness_score FLOAT NOT NULL DEFAULT 0.0,
    provenance_score FLOAT NOT NULL DEFAULT 0.0,
    overall_score FLOAT NOT NULL DEFAULT 0.0,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    details JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_md_quality_scores_entity ON md_quality_scores (global_entity_id, scored_at DESC);
"""


async def _ensure_db():
    admin = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database="salesos",
    )
    exists = await admin.fetchval("SELECT 1 FROM pg_database WHERE datname=$1", PG_DB)
    if not exists:
        await admin.execute(f"CREATE DATABASE {PG_DB} OWNER {PG_USER}")
    await admin.close()

    c = await _get_conn()
    await c.execute(PHASE0_DDL)
    tables = await c.fetch(
        "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
    )
    # Master Data source rows are protected by an append-only trigger.  This
    # integration suite owns the dedicated test database, so reset the full
    # md_* fixture with TRUNCATE (CASCADE) instead of issuing rejected DELETEs.
    names = [f'"{t["tablename"]}"' for t in tables]
    if names:
        await c.execute("TRUNCATE TABLE " + ", ".join(names) + " RESTART IDENTITY CASCADE")
    await c.close()


# ══════════════════════════════════════════════════════════════════════════════
# SCENARIO 1: Full ER pipeline — source rows → match → conflict
# ══════════════════════════════════════════════════════════════════════════════

class TestERIntegration:
    """Integration tests for Phase 3 ER pipeline against real PostgreSQL."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        await _ensure_db()
        self.conn = await _get_conn()
        yield
        await self.conn.close()

    # ── 1. Entity match creation ─────────────────────────────────────────

    async def test_01_entity_match_creation(self):
        entity_id = uuid.uuid4()
        match_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_entity_matches
            (id, global_entity_id, source_a_id, source_b_id, match_score, match_method,
             match_signals, match_status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'pending_review', $8)
            RETURNING id, match_score, match_method, match_status
            """,
            match_id, entity_id, "row-a", "row-b", 95.0, "cr_match",
            '[{"name":"cr_match","matched":true,"weight":100}]', now,
        )
        assert row is not None
        assert row["match_score"] == 95.0
        assert row["match_method"] == "cr_match"
        assert row["match_status"] == "pending_review"

    # ── 2. Entity conflict creation ──────────────────────────────────────

    async def test_02_entity_conflict_creation(self):
        entity_id = uuid.uuid4()
        conflict_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_entity_conflicts
            (id, global_entity_id, field_name, value_a, source_a_id,
             value_b, source_b_id, is_government_id, veto_enabled, resolution, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'open', $10)
            RETURNING id, field_name, value_a, value_b, resolution
            """,
            conflict_id, entity_id, "cr_number", "1010123456", "balady",
            "2020123456", "ncnp", True, True, now,
        )
        assert row is not None
        assert row["field_name"] == "cr_number"
        assert row["resolution"] == "open"

    # ── 3. Conflict resolution ───────────────────────────────────────────

    async def test_03_conflict_resolution(self):
        entity_id = uuid.uuid4()
        conflict_id = uuid.uuid4()
        now = datetime.now(UTC)

        await self.conn.execute(
            """
            INSERT INTO md_entity_conflicts
            (id, global_entity_id, field_name, value_a, source_a_id,
             value_b, source_b_id, resolution, created_at)
            VALUES ($1, $2, 'cr_number', '1010123456', 'balady',
                    '2020123456', 'ncnp', 'open', $3)
            """,
            conflict_id, entity_id, now,
        )

        await self.conn.execute(
            """
            UPDATE md_entity_conflicts SET resolution = 'resolved',
            resolved_value = '1010123456', resolved_by = $1, resolved_at = $2
            WHERE id = $3
            """,
            uuid.uuid4(), now, conflict_id,
        )

        row = await self.conn.fetchrow(
            "SELECT resolution, resolved_value FROM md_entity_conflicts WHERE id = $1",
            conflict_id,
        )
        assert row["resolution"] == "resolved"
        assert row["resolved_value"] == "1010123456"

    # ── 4. Merge history creation ────────────────────────────────────────

    async def test_04_merge_history_creation(self):
        import json
        target_id = uuid.uuid4()
        source_id = uuid.uuid4()
        history_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_entity_merge_history
            (id, operation, target_entity_id, source_entity_ids, performed_by,
             performed_at, rollback_available, details)
            VALUES ($1, 'merge', $2, $3, $4, $5, true, $6)
            RETURNING id, operation, target_entity_id, rollback_available
            """,
            history_id, target_id, json.dumps([str(source_id)]), uuid.uuid4(), now,
            json.dumps({"reason": "manual_merge"}),
        )
        assert row is not None
        assert row["operation"] == "merge"
        assert row["rollback_available"] is True

    # ── 5. Field provenance creation ─────────────────────────────────────

    async def test_05_field_provenance_creation(self):
        entity_id = uuid.uuid4()
        prov_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             source_file_id, evidence_tier, authority_score, selection_reason,
             conflict_status, is_current, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'none', true, $10)
            RETURNING id, field_name, field_value, evidence_tier, is_current
            """,
            prov_id, entity_id, "cr_number", "1010123456",
            uuid.uuid4(), uuid.uuid4(), "GOVERNMENT_ANCHOR", 1.0,
            "matched_signal", now,
        )
        assert row is not None
        assert row["field_name"] == "cr_number"
        assert row["is_current"] is True

    # ── 6. Field provenance supersede ────────────────────────────────────

    async def test_06_field_provenance_supersede(self):
        entity_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Insert first (current) value
        await self.conn.execute(
            """
            INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status, is_current, created_at)
            VALUES ($1, $2, 'canonical_name', 'شركة أ', $3, 'NORMALIZED_EXACT', 0.5,
                    'matched_signal', 'none', true, $4)
            """,
            uuid.uuid4(), entity_id, uuid.uuid4(), now,
        )

        # Supersede with higher authority
        await self.conn.execute(
            "UPDATE md_field_provenance SET is_current = false, superseded_at = $1 "
            "WHERE global_entity_id = $2 AND field_name = 'canonical_name' AND is_current = true",
            now, entity_id,
        )
        await self.conn.execute(
            """
            INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status, is_current, created_at)
            VALUES ($1, $2, 'canonical_name', 'شركة الراشد', $3, 'GOVERNMENT_ANCHOR', 1.0,
                    'matched_signal', 'none', true, $4)
            """,
            uuid.uuid4(), entity_id, uuid.uuid4(), now,
        )

        # Check current value is the new one
        row = await self.conn.fetchrow(
            "SELECT field_value, authority_score FROM md_field_provenance "
            "WHERE global_entity_id = $1 AND field_name = 'canonical_name' AND is_current = true",
            entity_id,
        )
        assert row["field_value"] == "شركة الراشد"
        assert row["authority_score"] == 1.0

        # Check old value is superseded
        old_row = await self.conn.fetchrow(
            "SELECT field_value, is_current FROM md_field_provenance "
            "WHERE global_entity_id = $1 AND field_name = 'canonical_name' AND field_value = 'شركة أ'",
            entity_id,
        )
        assert old_row["is_current"] is False

    # ── 7. Quality score creation ────────────────────────────────────────

    async def test_07_quality_score_creation(self):
        entity_id = uuid.uuid4()
        score_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_quality_scores
            (id, global_entity_id, completeness_score, accuracy_score,
             consistency_score, freshness_score, provenance_score,
             overall_score, scored_at, details)
            VALUES ($1, $2, 0.8, 0.9, 1.0, 0.6, 0.5, 0.78, $3, $4)
            RETURNING id, overall_score, completeness_score
            """,
            score_id, entity_id, now, '{"completeness": 0.8, "accuracy": 0.9}',
        )
        assert row is not None
        assert row["overall_score"] == 0.78
        assert row["completeness_score"] == 0.8

    # ── 8. Source row → match pipeline flow ──────────────────────────────

    async def test_08_source_rows_to_match_flow(self):
        """Full flow: create source rows with same CR → match persists."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        row_a_id = uuid.uuid4()
        row_b_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Create source file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "test.xlsx", "/test.xlsx", "f" * 64, 1024,
            "application/octet-stream", 1, 20, "test_source", tenant_id, now,
        )

        # Create two source rows with same CR number
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'balady', 'REC-1', 0,
                    '{"cr_number": "1010123456", "company_name": "شركة الراشد"}',
                    'company', 'pending', $4)
            """,
            row_a_id, tenant_id, file_id, now,
        )
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'ncnp', 'REC-2', 1,
                    '{"cr_number": "1010123456", "company_name": "الراشد للتجارة"}',
                    'company', 'pending', $4)
            """,
            row_b_id, tenant_id, file_id, now,
        )

        # Verify rows exist
        count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_source_rows WHERE source_file_id = $1", file_id
        )
        assert count == 2

        # Verify CR blocking key works (same CR → same group)
        cr_rows = await self.conn.fetch(
            "SELECT source_id, raw_payload->>'cr_number' AS cr FROM md_source_rows "
            "WHERE source_file_id = $1 ORDER BY row_number", file_id
        )
        assert len(cr_rows) == 2
        assert all(r["cr"] == "1010123456" for r in cr_rows)

    # ── 9. Match status filter query ─────────────────────────────────────

    async def test_09_match_status_filter(self):
        entity_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Insert matches with different statuses
        for status in ["pending_review", "auto_matched", "vetoed"]:
            await self.conn.execute(
                """
                INSERT INTO md_entity_matches
                (id, global_entity_id, source_a_id, source_b_id, match_score,
                 match_method, match_signals, match_status, created_at)
                VALUES ($1, $2, $3, $4, 80.0, 'cr_match', '[]', $5, $6)
                """,
                uuid.uuid4(), entity_id, f"row-{status}-a", f"row-{status}-b", status, now,
            )

        # Filter by status
        pending = await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_entity_matches WHERE match_status = 'pending_review'"
        )
        assert pending >= 1

        auto = await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_entity_matches WHERE match_status = 'auto_matched'"
        )
        assert auto >= 1

    # ── 10. Quality score ordering ───────────────────────────────────────

    async def test_10_quality_score_ordering(self):
        entity_id = uuid.uuid4()
        from datetime import timedelta

        # Insert multiple scores at different times
        for i in range(3):
            ts = datetime.now(UTC) + timedelta(seconds=i)
            await self.conn.execute(
                """
                INSERT INTO md_quality_scores
                (id, global_entity_id, completeness_score, accuracy_score,
                 consistency_score, freshness_score, provenance_score,
                 overall_score, scored_at, details)
                VALUES ($1, $2, $3, 0.5, 0.5, 0.5, 0.5, $3, $4, '{}')
                """,
                uuid.uuid4(), entity_id, float(i) / 10.0, ts,
            )

        # Latest score should be the one with highest overall (inserted last)
        latest = await self.conn.fetchrow(
            "SELECT overall_score FROM md_quality_scores "
            "WHERE global_entity_id = $1 ORDER BY scored_at DESC LIMIT 1",
            entity_id,
        )
        assert latest["overall_score"] == 0.2
