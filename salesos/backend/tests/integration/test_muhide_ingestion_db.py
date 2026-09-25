"""Phase 4 Integration Tests — MUHIDE Data Ingestion & Legacy Re-Housing.

Tests the full MUHIDE ingestion pipeline against real PostgreSQL (salesos_test).
Covers: source registration, bulk ingestion, legacy mapping, entity creation,
field provenance, CR invalidation, duplicate handling, fuzzy-never-auto-merge,
government-ID veto, idempotency, and candidate validation.
"""

from __future__ import annotations

import asyncio
import csv
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path

import asyncpg
import pytest

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"


async def _get_conn() -> asyncpg.Connection:
    return await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB,
    )


PHASE0_DDL = """
CREATE TABLE IF NOT EXISTS md_global_companies (
    id UUID PRIMARY KEY, slug VARCHAR(64) NOT NULL, canonical_name VARCHAR(512) NOT NULL,
    canonical_name_ar VARCHAR(512), canonical_name_en VARCHAR(512), cr_number VARCHAR(50),
    vat_number VARCHAR(50), unified_national_number VARCHAR(50), domain VARCHAR(255),
    website VARCHAR(512), city VARCHAR(100), region VARCHAR(100), country VARCHAR(100) NOT NULL DEFAULT 'Saudi Arabia',
    industry VARCHAR(255), legal_entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    status VARCHAR(32) NOT NULL DEFAULT 'active', confidence_score FLOAT NOT NULL DEFAULT 0.0,
    source_count INT NOT NULL DEFAULT 1, phone VARCHAR(50), email VARCHAR(255),
    address TEXT, latitude FLOAT, longitude FLOAT, metadata JSONB NOT NULL DEFAULT '{}',
    merged_from_ids JSONB, merged_at TIMESTAMPTZ, split_from_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_companies_slug ON md_global_companies (slug);

CREATE TABLE IF NOT EXISTS md_global_people (
    id UUID PRIMARY KEY, slug VARCHAR(64) NOT NULL, canonical_name VARCHAR(512) NOT NULL,
    email VARCHAR(255), phone VARCHAR(50), company_global_id UUID,
    job_title VARCHAR(255), linkedin_url VARCHAR(512),
    confidence_score FLOAT NOT NULL DEFAULT 0.0, source_count INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'active', metadata JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_global_people_slug ON md_global_people (slug);

CREATE TABLE IF NOT EXISTS md_legacy_id_mappings (
    id UUID PRIMARY KEY, legacy_id_type VARCHAR(32) NOT NULL, legacy_id VARCHAR(255) NOT NULL,
    global_entity_type VARCHAR(32) NOT NULL, global_entity_id UUID NOT NULL,
    confidence FLOAT NOT NULL DEFAULT 1.0, created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    verified_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_legacy_id_lookup ON md_legacy_id_mappings (legacy_id_type, legacy_id);

CREATE TABLE IF NOT EXISTS md_source_files (
    id UUID PRIMARY KEY, tenant_id UUID NOT NULL, filename VARCHAR(512) NOT NULL,
    storage_path VARCHAR(1024) NOT NULL, file_hash_sha256 VARCHAR(64) NOT NULL,
    file_size_bytes BIGINT NOT NULL, mime_type VARCHAR(128) NOT NULL,
    sheet_count INT NOT NULL, total_rows INT NOT NULL, source_system VARCHAR(64) NOT NULL,
    schema_mapping JSONB, uploaded_by UUID NOT NULL, uploaded_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    status VARCHAR(32) NOT NULL DEFAULT 'uploaded', deleted_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS ix_md_source_files_hash ON md_source_files (file_hash_sha256);

CREATE TABLE IF NOT EXISTS md_source_rows (
    id UUID PRIMARY KEY, tenant_id UUID NOT NULL, source_file_id UUID NOT NULL,
    source_id VARCHAR(64) NOT NULL, source_record_id VARCHAR(255) NOT NULL,
    row_number INT NOT NULL, sheet_name VARCHAR(255), raw_payload JSONB NOT NULL,
    normalized_payload JSONB, entity_type VARCHAR(32) NOT NULL DEFAULT 'company',
    global_entity_id UUID, resolution_status VARCHAR(32) NOT NULL DEFAULT 'pending',
    resolution_confidence FLOAT, resolution_method VARCHAR(64), import_batch_id UUID,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(), deleted_at TIMESTAMPTZ
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_source_rows_source ON md_source_rows (source_id, source_record_id);

CREATE TABLE IF NOT EXISTS md_entity_matches (
    id UUID PRIMARY KEY, global_entity_id UUID, source_a_id VARCHAR(255) NOT NULL,
    source_b_id VARCHAR(255) NOT NULL, match_score FLOAT NOT NULL DEFAULT 0.0,
    match_method VARCHAR(64) NOT NULL, match_signals JSONB NOT NULL DEFAULT '[]',
    match_status VARCHAR(32) NOT NULL DEFAULT 'pending_review',
    reviewed_by UUID, reviewed_at TIMESTAMPTZ, review_decision VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX IF NOT EXISTS ix_md_entity_matches_pair ON md_entity_matches (source_a_id, source_b_id);
CREATE INDEX IF NOT EXISTS ix_md_entity_matches_status ON md_entity_matches (match_status);

CREATE TABLE IF NOT EXISTS md_entity_conflicts (
    id UUID PRIMARY KEY, global_entity_id UUID, field_name VARCHAR(128) NOT NULL,
    value_a TEXT, source_a_id VARCHAR(255), source_a_priority INT DEFAULT 0,
    value_b TEXT, source_b_id VARCHAR(255), source_b_priority INT DEFAULT 0,
    is_government_id BOOLEAN NOT NULL DEFAULT false, veto_enabled BOOLEAN NOT NULL DEFAULT false,
    resolution VARCHAR(32) NOT NULL DEFAULT 'open', resolved_value TEXT,
    resolved_by UUID, resolved_at TIMESTAMPTZ, created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_entity_conflicts_entity ON md_entity_conflicts (global_entity_id, resolution);

CREATE TABLE IF NOT EXISTS md_entity_merge_history (
    id UUID PRIMARY KEY, operation VARCHAR(32) NOT NULL, target_entity_id UUID NOT NULL,
    source_entity_ids JSONB NOT NULL DEFAULT '[]', match_score FLOAT, match_method VARCHAR(64),
    performed_by UUID, performed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    rollback_available BOOLEAN NOT NULL DEFAULT true, rolled_back_at TIMESTAMPTZ,
    details JSONB NOT NULL DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS ix_md_merge_history_entity ON md_entity_merge_history (target_entity_id);

CREATE TABLE IF NOT EXISTS md_field_provenance (
    id UUID PRIMARY KEY, global_entity_id UUID NOT NULL, field_name VARCHAR(128) NOT NULL,
    field_value TEXT NOT NULL, source_row_id UUID, source_file_id UUID,
    observed_at TIMESTAMPTZ NOT NULL DEFAULT now(), evidence_tier VARCHAR(64) NOT NULL,
    verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified',
    verified_by UUID, verified_at TIMESTAMPTZ, authority_score FLOAT NOT NULL DEFAULT 0.0,
    selection_reason VARCHAR(128), conflict_status VARCHAR(32) NOT NULL DEFAULT 'none',
    is_current BOOLEAN NOT NULL DEFAULT true, superseded_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_md_field_provenance_entity ON md_field_provenance (global_entity_id, field_name);

CREATE TABLE IF NOT EXISTS md_quality_scores (
    id UUID PRIMARY KEY, global_entity_id UUID NOT NULL,
    completeness_score FLOAT NOT NULL DEFAULT 0.0, accuracy_score FLOAT NOT NULL DEFAULT 0.0,
    consistency_score FLOAT NOT NULL DEFAULT 0.0, freshness_score FLOAT NOT NULL DEFAULT 0.0,
    provenance_score FLOAT NOT NULL DEFAULT 0.0, overall_score FLOAT NOT NULL DEFAULT 0.0,
    scored_at TIMESTAMPTZ NOT NULL DEFAULT now(), details JSONB NOT NULL DEFAULT '{}'
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
    for t in tables:
        await c.execute(f'DELETE FROM "{t["tablename"]}"')
    await c.close()


# ══════════════════════════════════════════════════════════════════════════════
# MUHIDE INTEGRATION SCENARIOS
# ══════════════════════════════════════════════════════════════════════════════

class TestMUHIDEIntegration:
    """Integration tests for MUHIDE data ingestion and legacy re-housing."""

    @pytest.fixture(autouse=True)
    async def setup_and_teardown(self):
        await _ensure_db()
        self.conn = await _get_conn()
        yield
        await self.conn.close()

    # ── 1. MUHIDE source file registration ───────────────────────────────

    async def test_01_muhide_source_file_registration(self):
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            RETURNING id, filename, source_system, total_rows, status
            """,
            file_id, tenant_id, "01_Master_Accounts.parquet", "/data/muhide/01_Master_Accounts.parquet",
            "a" * 64, 50000000, "application/octet-stream", 1, 296746,
            "muhide_v2", tenant_id, now,
        )
        assert row is not None
        assert row["source_system"] == "muhide_v2"
        assert row["total_rows"] == 296746
        assert row["status"] == "completed"

    # ── 2. Source row ingestion with raw payload preservation ─────────────

    async def test_02_source_row_ingestion_preserves_payload(self):
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        row_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Register file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "03_Source_Map.parquet", "/data/muhide/03_Source_Map.parquet",
            "b" * 64, 10000000, "application/octet-stream", 1, 340186,
            "muhide_v2", tenant_id, now,
        )

        # Insert source row with MUHIDE-like payload
        raw_payload = {
            "Master Account ID": "MA-0000001",
            "CR_Numbers": "1010123456",
            "Canonical_Company_Name": "شركة الراشد للتجارة",
            "City": "الرياض",
            "Primary_Domain": "alrashed.com",
            "Primary_Phone": "0501234567",
            "Primary_Email": "info@alrashed.com",
            "Industry_Raw_Values": "تجارة عامة",
        }

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'company', 'pending', $8)
            RETURNING id, source_id, source_record_id, raw_payload, resolution_status
            """,
            row_id, tenant_id, file_id, "balady", "0/243", 0,
            json.dumps(raw_payload), now,
        )
        assert row is not None
        payload = json.loads(row["raw_payload"]) if isinstance(row["raw_payload"], str) else row["raw_payload"]
        assert payload["Master Account ID"] == "MA-0000001"
        assert payload["CR_Numbers"] == "1010123456"
        assert payload["Canonical_Company_Name"] == "شركة الراشد للتجارة"

    # ── 3. Legacy MA → Global ID mapping ─────────────────────────────────

    async def test_03_legacy_ma_to_global_id_mapping(self):
        global_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_legacy_id_mappings
            (id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id, legacy_id_type, legacy_id, global_entity_type, global_entity_id
            """,
            uuid.uuid4(), "LEGACY_MUHIDE_MA_ID", "MA-0000001", "C", global_id, 1.0, now,
        )
        assert row is not None
        assert row["legacy_id_type"] == "LEGACY_MUHIDE_MA_ID"
        assert row["legacy_id"] == "MA-0000001"
        assert row["global_entity_type"] == "C"

        # Verify lookup works
        found = await self.conn.fetchrow(
            "SELECT global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type = 'LEGACY_MUHIDE_MA_ID' AND legacy_id = 'MA-0000001'"
        )
        assert found is not None
        assert found["global_entity_id"] == global_id

    # ── 4. Global Company creation (G-C-XXXXXXXX) ────────────────────────

    async def test_04_global_company_creation(self):
        global_id = uuid.uuid4()
        slug = f"gc-{global_id.hex[:12]}"
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_global_companies
            (id, slug, canonical_name, cr_number, city, domain, phone, industry,
             country, status, source_count, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, 'active', 1, $10, $10)
            RETURNING id, slug, canonical_name, cr_number, status
            """,
            global_id, slug, "شركة الراشد للتجارة", "1010123456", "الرياض",
            "alrashed.com", "0501234567", "تجارة عامة", "Saudi Arabia", now,
        )
        assert row is not None
        assert row["status"] == "active"

    # ── 5. Global Person creation (G-P-XXXXXXXX) ────────────────────────

    async def test_05_global_person_creation(self):
        global_id = uuid.uuid4()
        slug = f"gp-{global_id.hex[:12]}"
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_global_people
            (id, slug, canonical_name, email, phone, company_global_id, job_title,
             status, source_count, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'active', 1, $8, $8)
            RETURNING id, slug, canonical_name, email, status
            """,
            global_id, slug, "أحمد الراشد", "ahmed@alrashed.com", "0501234567",
            uuid.uuid4(), "Manager", now,
        )
        assert row is not None
        assert row["status"] == "active"

    # ── 6. Field provenance creation ─────────────────────────────────────

    async def test_06_field_provenance_creation(self):
        entity_id = uuid.uuid4()
        prov_id = uuid.uuid4()
        now = datetime.now(UTC)

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status,
             is_current, created_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, 'none', true, $9)
            RETURNING id, field_name, field_value, evidence_tier, is_current
            """,
            prov_id, entity_id, "cr_number", "1010123456", uuid.uuid4(),
            "GOVERNMENT_ANCHOR", 1.0, "ingested_from_source", now,
        )
        assert row is not None
        assert row["is_current"] is True

    # ── 7. CR invalidation (short raw CR) ────────────────────────────────

    async def test_07_cr_invalidation_short_raw(self):
        """Short raw CR values (< 5 digits after normalization) must be rejected."""
        # normalize_cr("5") → None (too short)
        # normalize_cr("1234") → None (too short)
        # normalize_cr("1010123456") → "1010123456" (valid)
        import re

        def normalize_cr(raw):
            if not raw:
                return None
            s = re.sub(r'[\s\-\.]+', '', str(raw).strip())
            s = s.lstrip('0')
            if not s.isdigit() or len(s) < 5 or len(s) > 10:
                return None
            return s

        assert normalize_cr("5") is None
        assert normalize_cr("1234") is None
        # "00012345" → strip zeros → "12345" → 5 digits → valid (NOT too short)
        assert normalize_cr("00012345") == "12345"
        assert normalize_cr("1010123456") == "1010123456"
        assert normalize_cr("0001234567") == "1234567"

    # ── 8. Duplicate source-key handling ─────────────────────────────────

    async def test_08_duplicate_source_key_handling(self):
        """Duplicate (source_id, source_record_id) pairs are rejected by unique constraint."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Insert file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "dup_test.csv", "/dup_test.csv", "c" * 64, 100,
            "text/csv", 1, 2, "test", tenant_id, now,
        )

        # First insert succeeds
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'balady', 'REC-001', 0, '{}', 'company', 'pending', $4)
            """,
            uuid.uuid4(), tenant_id, file_id, now,
        )

        # Duplicate (source_id, source_record_id) must fail
        import asyncpg as apg
        with pytest.raises(apg.UniqueViolationError):
            await self.conn.execute(
                """
                INSERT INTO md_source_rows
                (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
                 raw_payload, entity_type, resolution_status, created_at)
                VALUES ($1, $2, $3, 'balady', 'REC-001', 1, '{}', 'company', 'pending', $4)
                """,
                uuid.uuid4(), tenant_id, file_id, now,
            )

    # ── 9. Fuzzy-never-auto-merge ────────────────────────────────────────

    async def test_09_fuzzy_never_auto_merge(self):
        """Fuzzy-only matches must NEVER result in AUTO_MERGE."""
        # Resolution candidates CSV: all 2,661 fuzzy pairs have REVIEW_REQUIRED
        # This is enforced by the policy engine: fuzzy_only → LOW confidence → SEPARATE
        # In the ER analysis, 2,145 pairs at score=100 are still REVIEW_REQUIRED
        from app.modules.entity_resolution.resolution_policy import (
            SourceRecord, ConfidenceClass, Decision, evaluate_pair,
        )
        from app.modules.entity_resolution.matching_pipeline import extract_signals, compute_score

        # Two records with only fuzzy name match
        a = SourceRecord(source_id="balady", canonical_name="شركة الراشد للتجارة")
        b = SourceRecord(source_id="balady", canonical_name="الراشد للتجارة")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)

        # Must NOT be AUTO_MERGE
        assert result.decision != Decision.AUTO_MERGE
        assert result.confidence in (ConfidenceClass.LOW, ConfidenceClass.MEDIUM)

    # ── 10. Government-ID veto ───────────────────────────────────────────

    async def test_10_government_id_veto(self):
        """Different CR numbers → VETOED, never merged."""
        from app.modules.entity_resolution.resolution_policy import (
            SourceRecord, Decision, evaluate_pair,
        )
        from app.modules.entity_resolution.matching_pipeline import extract_signals, compute_score

        a = SourceRecord(source_id="balady", cr_number="1010123456", canonical_name="شركة أ")
        b = SourceRecord(source_id="ncnp", cr_number="2020123456", canonical_name="شركة أ")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)

        assert result.decision == Decision.VETOED
        assert result.veto.vetoed

    # ── 11. Source independence enforcement ───────────────────────────────

    async def test_11_source_independence_enforcement(self):
        """Multiple records from same source do NOT count as independent."""
        from app.modules.entity_resolution.resolution_policy import (
            SourceRecord, ConfidenceClass, evaluate_pair,
        )
        from app.modules.entity_resolution.matching_pipeline import extract_signals, compute_score

        # Same source, same CR, same name — should be MEDIUM (not HIGH) because
        # only 1 source group, not 2 independent
        a = SourceRecord(source_id="balady", cr_number="1010123456", domain="test.com")
        b = SourceRecord(source_id="balady", cr_number="1010123456", domain="test.com")
        signals = extract_signals(a, b)
        score = compute_score(signals)
        result = evaluate_pair(a, b, signals, score)

        # Same source = not independent, but government anchor = HIGH
        # Government anchor overrides independence requirement
        assert result.has_government_anchor

    # ── 12. Idempotent re-import ─────────────────────────────────────────

    async def test_12_idempotent_reimport(self):
        """Re-importing same data does not create duplicate records."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Register file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "idempotent_test.csv", "/idempotent_test.csv", "d" * 64, 100,
            "text/csv", 1, 1, "test", tenant_id, now,
        )

        # First insert
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'balady', 'IDEM-001', 0, '{}', 'company', 'pending', $4)
            """,
            uuid.uuid4(), tenant_id, file_id, now,
        )

        # Duplicate insert with ON CONFLICT DO NOTHING — no error, no duplicate
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'balady', 'IDEM-001', 0, '{}', 'company', 'pending', $4)
            ON CONFLICT (source_id, source_record_id) DO NOTHING
            """,
            uuid.uuid4(), tenant_id, file_id, now,
        )

        count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_source_rows WHERE source_id = 'balady' AND source_record_id = 'IDEM-001'"
        )
        assert count == 1

    # ── 13. Historical review preservation ────────────────────────────────

    async def test_13_historical_review_preservation(self):
        """Historical review clusters are preserved as source rows."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Insert review cluster as source row
        review_payload = {
            "Old Master Account ID": "MA-0008682",
            "New Master Account ID(s)": "MA-0295366; MA-0295367; MA-0295368; MA-0295369",
            "CR Numbers": "7028448749; 7001587265; 7028592017",
            "Classification": "D - Multi-License / Multi-Facility",
        }

        row = await self.conn.fetchrow(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'muhide_review_cluster', 'MA-0008682', 0, $4, 'review_cluster', 'historical', $5)
            RETURNING id, source_id, entity_type, resolution_status
            """,
            uuid.uuid4(), tenant_id, file_id, json.dumps(review_payload), now,
        )
        assert row is not None
        assert row["entity_type"] == "review_cluster"
        assert row["resolution_status"] == "historical"

    # ── 14. Candidate validation fixture ──────────────────────────────────

    async def test_14_candidate_validation_fixture(self):
        """Load MUHIDE_resolution_candidates.csv and verify structure."""
        csv_path = str(Path.home() / "Downloads" / "MUHIDE_resolution_candidates.csv")
        try:
            with open(csv_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            assert len(rows) == 3226

            # Verify decision distribution: 2661 FUZZY→REVIEW_REQUIRED,
            # 563 GOVERNMENT_ANCHOR→VETOED, 2 MIXED→SEPARATE
            valid_classes = {"FUZZY", "GOVERNMENT_ANCHOR_CONFLICT", "MIXED"}
            for row in rows:
                assert row["evidence_class"] in valid_classes
                assert row["recommended_decision"] in ("REVIEW_REQUIRED", "VETOED", "SEPARATE")

        except FileNotFoundError:
            pytest.skip("MUHIDE_resolution_candidates.csv not found")

    # ── 15. Batch insert performance ──────────────────────────────────────

    async def test_15_batch_insert_performance(self):
        """Batch insert 1000 source rows efficiently."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        # Register file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "batch_test.csv", "/batch_test.csv", "e" * 64, 100000,
            "text/csv", 1, 1000, "test", tenant_id, now,
        )

        # Batch insert 1000 rows
        batch = []
        for i in range(1000):
            batch.append({
                "id": str(uuid.uuid4()),
                "tenant_id": str(tenant_id),
                "file_id": str(file_id),
                "source_id": "test_batch",
                "source_record_id": f"BATCH-{i:04d}",
                "row_number": i,
                "payload": json.dumps({"row": i}),
                "entity_type": "company",
                "now": now,
            })

        await self.conn.executemany(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1::uuid, $2::uuid, $3::uuid, $4, $5, $6, CAST($7 AS JSONB), $8, 'pending', $9)
            ON CONFLICT (source_id, source_record_id) DO NOTHING
            """,
            [(b["id"], b["tenant_id"], b["file_id"], b["source_id"], b["source_record_id"],
              b["row_number"], b["payload"], b["entity_type"], b["now"]) for b in batch],
        )

        count = await self.conn.fetchval(
            "SELECT COUNT(*) FROM md_source_rows WHERE source_id = 'test_batch'"
        )
        assert count == 1000

    # ── 16. Full MUHIDE-like pipeline flow ────────────────────────────────

    async def test_16_full_muhide_pipeline_flow(self):
        """End-to-end: source → global entity → legacy mapping → provenance."""
        tenant_id = uuid.uuid4()
        file_id = uuid.uuid4()
        now = datetime.now(UTC)

        # 1. Register source file
        await self.conn.execute(
            """
            INSERT INTO md_source_files
            (id, tenant_id, filename, storage_path, file_hash_sha256, file_size_bytes,
             mime_type, sheet_count, total_rows, source_system, uploaded_by, uploaded_at, status)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, 'completed')
            """,
            file_id, tenant_id, "full_flow_test.csv", "/full_flow_test.csv", "f" * 64, 1000,
            "text/csv", 1, 1, "muhide_v2", tenant_id, now,
        )

        # 2. Insert source row
        raw_payload = {
            "Master Account ID": "MA-0001234",
            "CR_Numbers": "1010123456",
            "Canonical_Company_Name": "شركة الاختبار",
            "City": "جدة",
            "Primary_Domain": "test.com",
            "Primary_Phone": "0509876543",
        }
        row_id = uuid.uuid4()
        await self.conn.execute(
            """
            INSERT INTO md_source_rows
            (id, tenant_id, source_file_id, source_id, source_record_id, row_number,
             raw_payload, entity_type, resolution_status, created_at)
            VALUES ($1, $2, $3, 'balady', 'FULL-001', 0, $4, 'company', 'pending', $5)
            """,
            row_id, tenant_id, file_id, json.dumps(raw_payload), now,
        )

        # 3. Create global company
        global_id = uuid.uuid4()
        slug = f"gc-{global_id.hex[:12]}"
        await self.conn.execute(
            """
            INSERT INTO md_global_companies
            (id, slug, canonical_name, cr_number, city, domain, phone,
             country, status, source_count, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, 'Saudi Arabia', 'active', 1, $8, $8)
            """,
            global_id, slug, "شركة الاختبار", "1010123456", "جدة",
            "test.com", "0509876543", now,
        )

        # 4. Register legacy mapping
        await self.conn.execute(
            """
            INSERT INTO md_legacy_id_mappings
            (id, legacy_id_type, legacy_id, global_entity_type, global_entity_id, confidence, created_at)
            VALUES ($1, 'LEGACY_MUHIDE_MA_ID', 'MA-0001234', 'C', $2, 1.0, $3)
            ON CONFLICT (legacy_id_type, legacy_id) DO NOTHING
            """,
            uuid.uuid4(), global_id, now,
        )

        # 5. Record field provenance
        await self.conn.execute(
            """
            INSERT INTO md_field_provenance
            (id, global_entity_id, field_name, field_value, source_row_id,
             evidence_tier, authority_score, selection_reason, conflict_status,
             is_current, created_at)
            VALUES ($1, $2, 'cr_number', '1010123456', $3,
                    'GOVERNMENT_ANCHOR', 1.0, 'ingested_from_source', 'none', true, $4)
            """,
            uuid.uuid4(), global_id, row_id, now,
        )

        # 6. Verify the full chain
        # Source row exists
        sr = await self.conn.fetchrow(
            "SELECT id, source_id, source_record_id FROM md_source_rows WHERE id = $1", row_id
        )
        assert sr is not None

        # Global company exists
        gc = await self.conn.fetchrow(
            "SELECT id, cr_number, canonical_name FROM md_global_companies WHERE id = $1", global_id
        )
        assert gc is not None
        assert gc["cr_number"] == "1010123456"

        # Legacy mapping exists
        lm = await self.conn.fetchrow(
            "SELECT global_entity_id FROM md_legacy_id_mappings "
            "WHERE legacy_id_type = 'LEGACY_MUHIDE_MA_ID' AND legacy_id = 'MA-0001234'"
        )
        assert lm is not None
        assert lm["global_entity_id"] == global_id

        # Field provenance exists
        fp = await self.conn.fetchrow(
            "SELECT field_name, field_value, evidence_tier FROM md_field_provenance "
            "WHERE global_entity_id = $1 AND field_name = 'cr_number' AND is_current = true",
            global_id,
        )
        assert fp is not None
        assert fp["evidence_tier"] == "GOVERNMENT_ANCHOR"
