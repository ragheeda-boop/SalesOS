"""Phase 6 — SCHEMA GATE for salesos_test (idempotent, rollback-safe).

Materializes the 11 missing master-data foundation tables (from the canonical
Alembic migration `j4k5l6m7n8o9_phase0_master_data_foundation.py`) plus the
Phase 6 specific derived tables, on **salesos_test only**.

Safety guarantees:
  - Only creates tables that DO NOT already exist (CREATE TABLE IF NOT EXISTS).
  - NEVER modifies existing tables or rows (11 existing md_* tables + 862,775
    source rows + 296,746 companies are untouched).
  - Idempotent: safe to run twice (no duplicate tables/rows/errors).
  - No RLS on the new global tables; RLS applied only to tenant-scoped ones
    (matching the canonical foundation migration).
  - Records alembic_version at a new head revision derived from j4k5l6m7n8o9.

Does NOT touch the `salesos` production database.
"""

from __future__ import annotations

import asyncio
import json
import sys
import uuid
from datetime import UTC, datetime

import asyncpg

PG_HOST = "localhost"
PG_PORT = 5432
PG_USER = "salesos"
PG_PASS = "salesos_dev_password"
PG_DB = "salesos_test"

# New head revision for this schema gate. Derives from j4k5l6m7n8o9.
NEW_HEAD = "p6a0b1c2d3e4"
PARENT = "j4k5l6m7n8o9"


# ═══════════════════════════════════════════════════════════════════════════
# The 11 missing foundation tables (columns copied verbatim from the canonical
# j4k5l6m7n8o9 migration so the test DB matches the source of truth).
# ═══════════════════════════════════════════════════════════════════════════

FOUNDATION_DDL = {
    "md_external_systems": """
        CREATE TABLE IF NOT EXISTS md_external_systems (
            id UUID PRIMARY KEY,
            system_key VARCHAR(64) NOT NULL,
            display_name VARCHAR(128) NOT NULL,
            supports_incremental BOOLEAN NOT NULL DEFAULT false,
            config JSONB NOT NULL DEFAULT '{}',
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_external_identities": """
        CREATE TABLE IF NOT EXISTS md_external_identities (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            tenant_id UUID NOT NULL,
            system_key VARCHAR(64) NOT NULL,
            object_type VARCHAR(64) NOT NULL,
            external_id VARCHAR(255) NOT NULL,
            external_name VARCHAR(512),
            external_url VARCHAR(1024),
            sync_status VARCHAR(32) NOT NULL DEFAULT 'synced',
            last_synced_at TIMESTAMPTZ,
            sync_metadata JSONB NOT NULL DEFAULT '{}',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_quality_issues": """
        CREATE TABLE IF NOT EXISTS md_quality_issues (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            issue_type VARCHAR(64) NOT NULL,
            field_name VARCHAR(255),
            description TEXT NOT NULL,
            severity VARCHAR(16) NOT NULL DEFAULT 'medium',
            status VARCHAR(32) NOT NULL DEFAULT 'open',
            assigned_to UUID,
            resolved_at TIMESTAMPTZ,
            resolution_notes TEXT,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_enrichment_tasks": """
        CREATE TABLE IF NOT EXISTS md_enrichment_tasks (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            current_value TEXT,
            missing_since TIMESTAMPTZ NOT NULL DEFAULT now(),
            priority INTEGER NOT NULL DEFAULT 100,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            enrichment_method VARCHAR(64),
            proposed_value TEXT,
            proposed_confidence FLOAT,
            evidence JSONB,
            approved_by UUID,
            approved_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_enrichment_evidence": """
        CREATE TABLE IF NOT EXISTS md_enrichment_evidence (
            id UUID PRIMARY KEY,
            task_id UUID,
            global_entity_id UUID NOT NULL,
            field_name VARCHAR(255) NOT NULL,
            value TEXT NOT NULL,
            source_type VARCHAR(32) NOT NULL,
            source_detail TEXT,
            confidence FLOAT NOT NULL,
            verification_status VARCHAR(32) NOT NULL DEFAULT 'unverified',
            verified_by UUID,
            verified_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_audit_events": """
        CREATE TABLE IF NOT EXISTS md_audit_events (
            id UUID PRIMARY KEY,
            global_entity_id UUID,
            event_type VARCHAR(64) NOT NULL,
            actor_id UUID,
            actor_type VARCHAR(32) NOT NULL DEFAULT 'user',
            old_value JSONB,
            new_value JSONB,
            source_record_id UUID,
            import_batch_id UUID,
            details JSONB,
            performed_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_ingestion_batches": """
        CREATE TABLE IF NOT EXISTS md_ingestion_batches (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            source_file_id UUID,
            import_type VARCHAR(32) NOT NULL,
            status VARCHAR(32) NOT NULL DEFAULT 'pending',
            total_rows INTEGER NOT NULL DEFAULT 0,
            imported_rows INTEGER NOT NULL DEFAULT 0,
            matched_entities INTEGER NOT NULL DEFAULT 0,
            new_entities INTEGER NOT NULL DEFAULT 0,
            conflict_rows INTEGER NOT NULL DEFAULT 0,
            rejected_rows INTEGER NOT NULL DEFAULT 0,
            review_rows INTEGER NOT NULL DEFAULT 0,
            changes_applied JSONB,
            rollback_available BOOLEAN NOT NULL DEFAULT true,
            rolled_back_at TIMESTAMPTZ,
            performed_by UUID NOT NULL,
            started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_tenant_entity_bindings": """
        CREATE TABLE IF NOT EXISTS md_tenant_entity_bindings (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            global_entity_id UUID NOT NULL,
            relationship_type VARCHAR(32) NOT NULL DEFAULT 'account',
            status VARCHAR(32) NOT NULL DEFAULT 'active',
            owner_id UUID,
            tenant_specific_name VARCHAR(512),
            tenant_specific_data JSONB NOT NULL DEFAULT '{}',
            source_binding_id UUID,
            bound_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_tenant_entity_attributes": """
        CREATE TABLE IF NOT EXISTS md_tenant_entity_attributes (
            id UUID PRIMARY KEY,
            binding_id UUID NOT NULL,
            attribute_name VARCHAR(255) NOT NULL,
            attribute_value TEXT,
            source VARCHAR(64) NOT NULL DEFAULT 'manual',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_sharing_policies": """
        CREATE TABLE IF NOT EXISTS md_sharing_policies (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            policy_name VARCHAR(255) NOT NULL,
            policy_version INTEGER NOT NULL DEFAULT 1,
            shared_categories JSONB NOT NULL DEFAULT '[]',
            excluded_categories JSONB NOT NULL DEFAULT '[]',
            effective_from TIMESTAMPTZ NOT NULL,
            effective_until TIMESTAMPTZ,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_by UUID NOT NULL,
            approved_by UUID,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
    "md_sharing_consents": """
        CREATE TABLE IF NOT EXISTS md_sharing_consents (
            id UUID PRIMARY KEY,
            tenant_id UUID NOT NULL,
            policy_id UUID NOT NULL,
            global_entity_id UUID NOT NULL,
            consent_status VARCHAR(32) NOT NULL DEFAULT 'granted',
            consented_by UUID NOT NULL,
            consented_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            revoked_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """,
}


# Canonical indexes for the 11 missing foundation tables (from j4k5l6m7n8o9).
FOUNDATION_INDEXES = {
    "md_external_systems": [
        ("ix_md_external_systems_key",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_md_external_systems_key ON md_external_systems (system_key)"),
    ],
    "md_external_identities": [
        ("ix_md_external_identities_unique",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_md_external_identities_unique ON md_external_identities (tenant_id, system_key, object_type, external_id)"),
        ("ix_md_external_global",
         "CREATE INDEX IF NOT EXISTS ix_md_external_global ON md_external_identities (global_entity_id)"),
        ("ix_md_external_tenant_system",
         "CREATE INDEX IF NOT EXISTS ix_md_external_tenant_system ON md_external_identities (tenant_id, system_key)"),
    ],
    "md_quality_issues": [
        ("ix_md_quality_issues_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_quality_issues_entity ON md_quality_issues (global_entity_id, status)"),
        ("ix_md_quality_issues_type",
         "CREATE INDEX IF NOT EXISTS ix_md_quality_issues_type ON md_quality_issues (issue_type, status)"),
        ("ix_md_quality_issues_severity",
         "CREATE INDEX IF NOT EXISTS ix_md_quality_issues_severity ON md_quality_issues (severity, status)"),
    ],
    "md_enrichment_tasks": [
        ("ix_md_enrichment_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_enrichment_entity ON md_enrichment_tasks (global_entity_id, status)"),
        ("ix_md_enrichment_priority",
         "CREATE INDEX IF NOT EXISTS ix_md_enrichment_priority ON md_enrichment_tasks (priority, status) WHERE status = 'pending'"),
    ],
    "md_enrichment_evidence": [
        ("ix_md_enrichment_evidence_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_enrichment_evidence_entity ON md_enrichment_evidence (global_entity_id, field_name)"),
        ("ix_md_enrichment_evidence_task",
         "CREATE INDEX IF NOT EXISTS ix_md_enrichment_evidence_task ON md_enrichment_evidence (task_id)"),
    ],
    "md_audit_events": [
        ("ix_md_audit_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_audit_entity ON md_audit_events (global_entity_id, performed_at DESC)"),
        ("ix_md_audit_type",
         "CREATE INDEX IF NOT EXISTS ix_md_audit_type ON md_audit_events (event_type, performed_at DESC)"),
        ("ix_md_audit_batch",
         "CREATE INDEX IF NOT EXISTS ix_md_audit_batch ON md_audit_events (import_batch_id)"),
        ("ix_md_audit_performed",
         "CREATE INDEX IF NOT EXISTS ix_md_audit_performed ON md_audit_events (performed_at DESC)"),
    ],
    "md_ingestion_batches": [
        ("ix_md_ingestion_batches_tenant",
         "CREATE INDEX IF NOT EXISTS ix_md_ingestion_batches_tenant ON md_ingestion_batches (tenant_id, started_at DESC)"),
        ("ix_md_ingestion_batches_status",
         "CREATE INDEX IF NOT EXISTS ix_md_ingestion_batches_status ON md_ingestion_batches (status)"),
    ],
    "md_tenant_entity_bindings": [
        ("ix_md_bindings_unique",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_md_bindings_unique ON md_tenant_entity_bindings (tenant_id, global_entity_id)"),
        ("ix_md_bindings_tenant",
         "CREATE INDEX IF NOT EXISTS ix_md_bindings_tenant ON md_tenant_entity_bindings (tenant_id, status)"),
        ("ix_md_bindings_global",
         "CREATE INDEX IF NOT EXISTS ix_md_bindings_global ON md_tenant_entity_bindings (global_entity_id)"),
        ("ix_md_bindings_relationship",
         "CREATE INDEX IF NOT EXISTS ix_md_bindings_relationship ON md_tenant_entity_bindings (relationship_type)"),
    ],
    "md_tenant_entity_attributes": [
        ("ix_md_attributes_unique",
         "CREATE UNIQUE INDEX IF NOT EXISTS ix_md_attributes_unique ON md_tenant_entity_attributes (binding_id, attribute_name)"),
    ],
    "md_sharing_policies": [
        ("ix_md_sharing_policies_tenant",
         "CREATE INDEX IF NOT EXISTS ix_md_sharing_policies_tenant ON md_sharing_policies (tenant_id, is_active)"),
    ],
    "md_sharing_consents": [
        ("ix_md_sharing_consents_tenant",
         "CREATE INDEX IF NOT EXISTS ix_md_sharing_consents_tenant ON md_sharing_consents (tenant_id, consent_status)"),
        ("ix_md_sharing_consents_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_sharing_consents_entity ON md_sharing_consents (global_entity_id)"),
    ],
}


# ═══════════════════════════════════════════════════════════════════════════
# Phase 6 SPECIFIC derived tables.
#
# These satisfy the versioned/history-preserving, evidence-first requirements
# of the DI contract. All are GLOBAL (no RLS) — app-layer ACL as with the other
# global tables. All keyed idempotently with deterministic unique constraints.
# ═══════════════════════════════════════════════════════════════════════════

PHASE6_DDL = {
    # Corrected (OPTION C) identity + sales-readiness classification, versioned.
    "md_identity_classifications": """
        CREATE TABLE IF NOT EXISTS md_identity_classifications (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            classification_version VARCHAR(32) NOT NULL,
            identity_state VARCHAR(40) NOT NULL,
            sales_readiness VARCHAR(40) NOT NULL,
            review_priority VARCHAR(4) NOT NULL,
            cr_class VARCHAR(24),
            has_cr BOOLEAN NOT NULL DEFAULT false,
            has_vat BOOLEAN NOT NULL DEFAULT false,
            has_unified BOOLEAN NOT NULL DEFAULT false,
            has_real_domain BOOLEAN NOT NULL DEFAULT false,
            independent_source_count INTEGER NOT NULL DEFAULT 1,
            source_count INTEGER NOT NULL DEFAULT 1,
            conflicts BOOLEAN NOT NULL DEFAULT false,
            signals JSONB NOT NULL DEFAULT '{}',
            source_ids JSONB NOT NULL DEFAULT '[]',
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_identity_class UNIQUE (global_entity_id, classification_version)
        )
    """,
    # Priority candidates / review queues (P0/P1/P2/P3) — prioritization only.
    "md_review_candidates": """
        CREATE TABLE IF NOT EXISTS md_review_candidates (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            candidate_type VARCHAR(4) NOT NULL,
            priority_score INTEGER NOT NULL DEFAULT 0,
            reason VARCHAR(255) NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}',
            source_ids JSONB NOT NULL DEFAULT '[]',
            status VARCHAR(24) NOT NULL DEFAULT 'pending',
            decision VARCHAR(24),
            decided_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_review_candidate UNIQUE (global_entity_id, candidate_type, reason)
        )
    """,
    # P0 dispositions (MATCH / SEPARATE / VETOED only; no auto resolution).
    "md_p0_dispositions": """
        CREATE TABLE IF NOT EXISTS md_p0_dispositions (
            id UUID PRIMARY KEY,
            conflict_id UUID NOT NULL,
            global_entity_id UUID NOT NULL,
            disposition VARCHAR(12) NOT NULL,
            reviewer VARCHAR(255) NOT NULL,
            reviewed_at TIMESTAMPTZ NOT NULL,
            reason TEXT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}',
            previous_state JSONB NOT NULL DEFAULT '{}',
            new_state JSONB NOT NULL DEFAULT '{}',
            source_records JSONB NOT NULL DEFAULT '[]',
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_p0_disposition UNIQUE (conflict_id, reviewer)
        )
    """,
    # Industry normalization — raw kept immutable, normalized stored separately.
    "md_industry_normalization": """
        CREATE TABLE IF NOT EXISTS md_industry_normalization (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            raw_industry TEXT NOT NULL,
            normalized_industry VARCHAR(255),
            industry_code VARCHAR(64),
            normalization_method VARCHAR(64) NOT NULL,
            source_row_id UUID,
            is_current BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_industry_norm UNIQUE (global_entity_id, raw_industry, normalization_method)
        )
    """,
    # Contact <-> company relationship evidence (INFERRED / VERIFIED + basis).
    "md_contact_relationships": """
        CREATE TABLE IF NOT EXISTS md_contact_relationships (
            id UUID PRIMARY KEY,
            person_global_id UUID NOT NULL,
            company_global_id UUID NOT NULL,
            relationship_type VARCHAR(32) NOT NULL DEFAULT 'account',
            status VARCHAR(16) NOT NULL DEFAULT 'INFERRED',
            linking_basis VARCHAR(64) NOT NULL,
            confidence FLOAT NOT NULL,
            evidence JSONB NOT NULL DEFAULT '{}',
            source_id VARCHAR(64),
            observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_contact_rel UNIQUE (person_global_id, company_global_id, linking_basis)
        )
    """,
    # Versioned quality recalculation (preserves previous + version).
    "md_quality_score_history": """
        CREATE TABLE IF NOT EXISTS md_quality_score_history (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            calc_version VARCHAR(32) NOT NULL,
            completeness_score FLOAT NOT NULL DEFAULT 0.0,
            accuracy_score FLOAT NOT NULL DEFAULT 0.0,
            consistency_score FLOAT NOT NULL DEFAULT 0.0,
            freshness_score FLOAT NOT NULL DEFAULT 0.0,
            provenance_score FLOAT NOT NULL DEFAULT 0.0,
            overall_score FLOAT NOT NULL DEFAULT 0.0,
            evidence_basis JSONB NOT NULL DEFAULT '{}',
            previous_version VARCHAR(32),
            previous_overall FLOAT,
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_quality_hist UNIQUE (global_entity_id, calc_version)
        )
    """,
    # Versioned sales-readiness recalculation (preserves previous).
    "md_sales_readiness_history": """
        CREATE TABLE IF NOT EXISTS md_sales_readiness_history (
            id UUID PRIMARY KEY,
            global_entity_id UUID NOT NULL,
            calc_version VARCHAR(32) NOT NULL,
            sales_readiness VARCHAR(40) NOT NULL,
            identity_state VARCHAR(40) NOT NULL,
            basis JSONB NOT NULL DEFAULT '{}',
            previous_version VARCHAR(32),
            previous_readiness VARCHAR(40),
            computed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_md_sales_readiness UNIQUE (global_entity_id, calc_version)
        )
    """,
}

PHASE6_INDEXES = {
    "md_identity_classifications": [
        ("ix_md_identity_class_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_identity_class_entity ON md_identity_classifications (global_entity_id)"),
        ("ix_md_identity_class_state",
         "CREATE INDEX IF NOT EXISTS ix_md_identity_class_state ON md_identity_classifications (identity_state)"),
    ],
    "md_review_candidates": [
        ("ix_md_review_candidate_type",
         "CREATE INDEX IF NOT EXISTS ix_md_review_candidate_type ON md_review_candidates (candidate_type, status)"),
    ],
    "md_p0_dispositions": [
        ("ix_md_p0_disposition_conflict",
         "CREATE INDEX IF NOT EXISTS ix_md_p0_disposition_conflict ON md_p0_dispositions (conflict_id)"),
    ],
    "md_industry_normalization": [
        ("ix_md_industry_norm_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_industry_norm_entity ON md_industry_normalization (global_entity_id, is_current)"),
    ],
    "md_contact_relationships": [
        ("ix_md_contact_rel_person",
         "CREATE INDEX IF NOT EXISTS ix_md_contact_rel_person ON md_contact_relationships (person_global_id)"),
        ("ix_md_contact_rel_company",
         "CREATE INDEX IF NOT EXISTS ix_md_contact_rel_company ON md_contact_relationships (company_global_id)"),
    ],
    "md_quality_score_history": [
        ("ix_md_quality_hist_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_quality_hist_entity ON md_quality_score_history (global_entity_id)"),
    ],
    "md_sales_readiness_history": [
        ("ix_md_sales_readiness_entity",
         "CREATE INDEX IF NOT EXISTS ix_md_sales_readiness_entity ON md_sales_readiness_history (global_entity_id)"),
    ],
}


# RLS: tenant-scoped foundation tables + none of the new Phase 6 tables
# (they are GLOBAL per DI contract §canonical/global authority).
RLS_TABLES = [
    "md_source_files",
    "md_source_rows",
    "md_external_identities",
    "md_ingestion_batches",
    "md_tenant_entity_bindings",
    "md_sharing_policies",
    "md_sharing_consents",
]
# FK-based RLS via parent.
RLS_PARENT_TABLES = ["md_tenant_entity_attributes"]


def _rl_sql():
    sql = []
    sess = "app.tenant_id"
    for t in RLS_TABLES:
        sql.append(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY')
        sql.append(f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY')
        sql.append(f'DROP POLICY IF EXISTS "tenant_isolation_{t}" ON "{t}"')
        sql.append(
            f'CREATE POLICY "tenant_isolation_{t}" ON "{t}" FOR ALL '
            f"USING (tenant_id::text = current_setting('{sess}', true)) "
            f"WITH CHECK (tenant_id::text = current_setting('{sess}', true))"
        )
    # md_source_values has no tenant_id; isolate it through its source row.
    t = "md_source_values"
    sql.append(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY')
    sql.append(f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY')
    sql.append(f'DROP POLICY IF EXISTS "tenant_isolation_{t}" ON "{t}"')
    sql.append(
        f'CREATE POLICY "tenant_isolation_{t}" ON "{t}" FOR ALL '
        f"USING (EXISTS (SELECT 1 FROM \"md_source_rows\" sr "
        f"WHERE sr.id = {t}.source_row_id "
        f"AND sr.tenant_id::text = current_setting('{sess}', true))) "
        f"WITH CHECK (EXISTS (SELECT 1 FROM \"md_source_rows\" sr "
        f"WHERE sr.id = {t}.source_row_id "
        f"AND sr.tenant_id::text = current_setting('{sess}', true)))"
    )
    # md_tenant_entity_attributes via parent md_tenant_entity_bindings
    t = "md_tenant_entity_attributes"
    sql.append(f'ALTER TABLE "{t}" ENABLE ROW LEVEL SECURITY')
    sql.append(f'ALTER TABLE "{t}" FORCE ROW LEVEL SECURITY')
    sql.append(f'DROP POLICY IF EXISTS "tenant_isolation_{t}" ON "{t}"')
    sql.append(
        f'CREATE POLICY "tenant_isolation_{t}" ON "{t}" FOR ALL '
        f"USING (EXISTS (SELECT 1 FROM \"md_tenant_entity_bindings\" b "
        f"WHERE b.id = {t}.binding_id "
        f"AND b.tenant_id::text = current_setting('{sess}', true))) "
        f"WITH CHECK (EXISTS (SELECT 1 FROM \"md_tenant_entity_bindings\" b "
        f"WHERE b.id = {t}.binding_id "
        f"AND b.tenant_id::text = current_setting('{sess}', true)))"
    )
    return sql


def _source_immutability_sql():
    """Install append-only guards while allowing derived linkage updates."""
    return [
        """CREATE OR REPLACE FUNCTION md_guard_source_immutability()
        RETURNS trigger AS $$
        BEGIN
            IF TG_OP = 'DELETE' THEN
                RAISE EXCEPTION 'source evidence rows are append-only';
            END IF;
            IF TG_TABLE_NAME = 'md_source_files' THEN
                IF ROW(NEW.id, NEW.tenant_id, NEW.filename, NEW.storage_path,
                       NEW.file_hash_sha256, NEW.file_size_bytes, NEW.mime_type,
                       NEW.sheet_count, NEW.total_rows, NEW.source_system,
                       NEW.schema_mapping, NEW.uploaded_by, NEW.uploaded_at, NEW.deleted_at)
                   IS DISTINCT FROM
                   ROW(OLD.id, OLD.tenant_id, OLD.filename, OLD.storage_path,
                       OLD.file_hash_sha256, OLD.file_size_bytes, OLD.mime_type,
                       OLD.sheet_count, OLD.total_rows, OLD.source_system,
                       OLD.schema_mapping, OLD.uploaded_by, OLD.uploaded_at, OLD.deleted_at) THEN
                    RAISE EXCEPTION 'source file identity and metadata are immutable';
                END IF;
            ELSIF TG_TABLE_NAME = 'md_source_rows' THEN
                IF ROW(NEW.id, NEW.tenant_id, NEW.source_file_id, NEW.source_id,
                       NEW.source_record_id, NEW.row_number, NEW.sheet_name,
                       NEW.raw_payload, NEW.entity_type, NEW.created_at, NEW.deleted_at)
                   IS DISTINCT FROM
                   ROW(OLD.id, OLD.tenant_id, OLD.source_file_id, OLD.source_id,
                       OLD.source_record_id, OLD.row_number, OLD.sheet_name,
                       OLD.raw_payload, OLD.entity_type, OLD.created_at, OLD.deleted_at) THEN
                    RAISE EXCEPTION 'source row identity and raw payload are immutable';
                END IF;
            ELSIF TG_TABLE_NAME = 'md_source_values' THEN
                IF ROW(NEW.id, NEW.source_row_id, NEW.field_name,
                       NEW.original_value, NEW.created_at)
                   IS DISTINCT FROM
                   ROW(OLD.id, OLD.source_row_id, OLD.field_name,
                       OLD.original_value, OLD.created_at) THEN
                    RAISE EXCEPTION 'source value identity and original value are immutable';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql""",
        'DROP TRIGGER IF EXISTS trg_md_source_files_immutable ON "md_source_files"',
        'CREATE TRIGGER trg_md_source_files_immutable BEFORE UPDATE OR DELETE ON "md_source_files" FOR EACH ROW EXECUTE FUNCTION md_guard_source_immutability()',
        'DROP TRIGGER IF EXISTS trg_md_source_rows_immutable ON "md_source_rows"',
        'CREATE TRIGGER trg_md_source_rows_immutable BEFORE UPDATE OR DELETE ON "md_source_rows" FOR EACH ROW EXECUTE FUNCTION md_guard_source_immutability()',
        'DROP TRIGGER IF EXISTS trg_md_source_values_immutable ON "md_source_values"',
        'CREATE TRIGGER trg_md_source_values_immutable BEFORE UPDATE OR DELETE ON "md_source_values" FOR EACH ROW EXECUTE FUNCTION md_guard_source_immutability()',
    ]


async def main() -> int:
    conn = await asyncpg.connect(
        host=PG_HOST, port=PG_PORT, user=PG_USER, password=PG_PASS, database=PG_DB
    )
    try:
        db = await conn.fetchval("SELECT current_database()")
        assert db == "salesos_test", f"REFUSING: connected to {db}, not salesos_test"
        print(f"Connected to {db} (safe).")

        # Snapshot current table state BEFORE any change (existing 11 untouched).
        before = set(
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
            )
        )
        before_count = await conn.fetchval(
            "SELECT COUNT(*) FROM md_source_rows"
        )
        before_companies = await conn.fetchval(
            "SELECT COUNT(*) FROM md_global_companies"
        )
        print(f"Before: {len(before)} md_ tables, source_rows={before_count:,}, companies={before_companies:,}")

        created = []
        # 1. Create the 11 missing foundation tables (idempotent).
        for t, ddl in FOUNDATION_DDL.items():
            if t not in before:
                await conn.execute(ddl)
                created.append(t)
        # 2. Create Phase 6 specific tables (idempotent).
        for t, ddl in PHASE6_DDL.items():
            if t not in before:
                await conn.execute(ddl)
                created.append(t)

        # 3. Indexes for newly created foundation tables.
        for t, idxs in FOUNDATION_INDEXES.items():
            for _, ddl in idxs:
                await conn.execute(ddl)
        # 4. Indexes for Phase 6 tables.
        for t, idxs in PHASE6_INDEXES.items():
            for _, ddl in idxs:
                await conn.execute(ddl)

        # 5. RLS on tenant-scoped tables.
        for sql in _rl_sql():
            await conn.execute(sql)

        # 5b. Preserve immutable source evidence at the database boundary.
        for sql in _source_immutability_sql():
            await conn.execute(sql)

        # 6. Stamp alembic_version at the new head (idempotent — only first run).
        ver_exists = await conn.fetchval(
            "SELECT to_regclass('public.alembic_version')"
        )
        if not ver_exists:
            await conn.execute(
                "CREATE TABLE alembic_version (version_num varchar(32) NOT NULL)"
            )
            await conn.execute(
                "ALTER TABLE alembic_version ADD CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)"
            )
            await conn.execute(
                "INSERT INTO alembic_version (version_num) VALUES ($1) ON CONFLICT DO NOTHING",
                NEW_HEAD,
            )
            print(f"Stamped alembic_version = {NEW_HEAD}")
        else:
            cur = await conn.fetchval("SELECT version_num FROM alembic_version LIMIT 1")
            print(f"alembic_version already present: {cur} (no-op)")

        await conn.execute("COMMIT")

        # ── VERIFY ─────────────────────────────────────────────────────────
        after = set(
            r["tablename"]
            for r in await conn.fetch(
                "SELECT tablename FROM pg_tables WHERE schemaname='public' AND tablename LIKE 'md_%'"
            )
        )
        after_count = await conn.fetchval("SELECT COUNT(*) FROM md_source_rows")
        after_companies = await conn.fetchval("SELECT COUNT(*) FROM md_global_companies")

        print("\n=== VERIFY ===")
        print(f"Created tables: {created}")
        print(f"md_ tables before={len(before)} after={len(after)} (delta={len(after)-len(before)})")
        print(f"source_rows before={before_count:,} after={after_count:,}  (must be equal)")
        print(f"companies  before={before_companies:,} after={after_companies:,} (must be equal)")

        ok = True
        missing = {f"md_{i:02d}_dummy" for i in range(0)}  # placeholder
        # Verify all 22 foundation + 7 Phase6 tables exist.
        expected = (
            {"md_global_companies","md_global_people","md_legacy_id_mappings",
             "md_entity_matches","md_entity_conflicts","md_entity_merge_history",
             "md_field_provenance","md_quality_scores","md_source_files",
             "md_source_rows","md_source_values",
             "md_external_systems","md_external_identities","md_quality_issues",
             "md_enrichment_tasks","md_enrichment_evidence","md_audit_events",
             "md_ingestion_batches","md_tenant_entity_bindings",
             "md_tenant_entity_attributes","md_sharing_policies","md_sharing_consents"}
        ) | set(PHASE6_DDL.keys())
        absent = expected - after
        if absent:
            ok = False
            print(f"  MISSING: {absent}")
        if before_count != after_count or before_companies != after_companies:
            ok = False
            print("  DATA CHANGED (source_rows or companies)")

        # Verify tenant-scoped source tables are protected and global master
        # tables remain intentionally outside tenant RLS.
        rls_state = await conn.fetch(
            "SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = ANY($1::text[])",
            ["md_source_files", "md_source_rows", "md_source_values"],
        )
        rls_by_table = {r["relname"]: (r["relrowsecurity"], r["relforcerowsecurity"]) for r in rls_state}
        expected_source_tables = {"md_source_files", "md_source_rows", "md_source_values"}
        if set(rls_by_table) != expected_source_tables or any(
            state != (True, True) for state in rls_by_table.values()
        ):
            ok = False
            print(f"  SOURCE RLS FAILED: {rls_by_table}")
        else:
            print("  Source RLS: ENABLED + FORCED on files, rows, and values")

        global_state = await conn.fetch(
            "SELECT c.relname, c.relrowsecurity "
            "FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace "
            "WHERE n.nspname='public' AND c.relname = ANY($1::text[])",
            ["md_global_companies", "md_global_people", "md_legacy_id_mappings"],
        )
        unexpected_global_rls = [r["relname"] for r in global_state if r["relrowsecurity"]]
        if unexpected_global_rls:
            ok = False
            print(f"  GLOBAL RLS UNEXPECTED: {unexpected_global_rls}")
        else:
            print("  Global master tables: no tenant RLS (expected)")

        source_triggers = await conn.fetchval(
            "SELECT count(*) FROM pg_trigger "
            "WHERE NOT tgisinternal AND tgname = ANY($1::text[])",
            ["trg_md_source_files_immutable", "trg_md_source_rows_immutable", "trg_md_source_values_immutable"],
        )
        if source_triggers != 3:
            ok = False
            print(f"  SOURCE IMMUTABILITY TRIGGERS FAILED: found {source_triggers}/3")
        else:
            print("  Source immutability: update/delete guards installed on all 3 source tables")

        role_privileges = await conn.fetchrow(
            """SELECT r.rolsuper, r.rolbypassrls,
               has_table_privilege('salesos_app', 'md_source_files', 'SELECT') AS file_select,
               has_table_privilege('salesos_app', 'md_source_files', 'INSERT') AS file_insert,
               has_column_privilege('salesos_app', 'md_source_files', 'status', 'UPDATE') AS file_status_update,
               has_column_privilege('salesos_app', 'md_source_files', 'filename', 'UPDATE') AS file_name_update,
               has_table_privilege('salesos_app', 'md_source_files', 'DELETE') AS file_delete,
               has_table_privilege('salesos_app', 'md_source_rows', 'SELECT') AS row_select,
               has_table_privilege('salesos_app', 'md_source_rows', 'INSERT') AS row_insert,
               has_column_privilege('salesos_app', 'md_source_rows', 'global_entity_id', 'UPDATE') AS row_link_update,
               has_column_privilege('salesos_app', 'md_source_rows', 'raw_payload', 'UPDATE') AS row_payload_update,
               has_table_privilege('salesos_app', 'md_source_rows', 'DELETE') AS row_delete,
               has_table_privilege('salesos_app', 'md_source_values', 'SELECT') AS value_select,
               has_table_privilege('salesos_app', 'md_source_values', 'INSERT') AS value_insert,
               has_column_privilege('salesos_app', 'md_source_values', 'original_value', 'UPDATE') AS original_value_update,
               has_table_privilege('salesos_app', 'md_source_values', 'DELETE') AS value_delete
               FROM pg_roles r WHERE r.rolname='salesos_app'"""
        )
        expected_privileges = {
            "rolsuper": False,
            "rolbypassrls": False,
            "file_select": True,
            "file_insert": True,
            "file_status_update": True,
            "file_name_update": False,
            "file_delete": False,
            "row_select": True,
            "row_insert": True,
            "row_link_update": True,
            "row_payload_update": False,
            "row_delete": False,
            "value_select": True,
            "value_insert": True,
            "original_value_update": False,
            "value_delete": False,
        }
        if not role_privileges or any(
            role_privileges[key] is not expected for key, expected in expected_privileges.items()
        ):
            ok = False
            print(f"  APP ROLE SOURCE PRIVILEGES FAILED: {dict(role_privileges) if role_privileges else None}")
        else:
            print("  App role: source SELECT/INSERT only; permitted updates are limited to file status and row linkage")

        # Exercise the guards against an existing source row. Each rejected
        # mutation is rolled back to a savepoint; no source values are changed.
        probe_row_id = await conn.fetchval("SELECT id FROM md_source_rows LIMIT 1")
        if probe_row_id:
            await conn.execute("BEGIN")
            for label, statement in (
                (
                    "raw_payload update",
                    "UPDATE md_source_rows SET raw_payload = raw_payload || '{\"_probe\":true}'::jsonb WHERE id=$1",
                ),
                ("source row delete", "DELETE FROM md_source_rows WHERE id=$1"),
            ):
                await conn.execute("SAVEPOINT source_immutability_probe")
                try:
                    await conn.execute(statement, probe_row_id)
                    ok = False
                    print(f"  IMMUTABILITY FAILED: {label} was accepted")
                except Exception:
                    await conn.execute("ROLLBACK TO SAVEPOINT source_immutability_probe")
            await conn.execute("ROLLBACK")
            if ok:
                print("  Source immutability probes: raw_payload update and row delete rejected")
        else:
            print("  Source immutability probes: skipped (no source rows to probe)")

        # Idempotency probe: rerun table creation should not error / change count.
        try:
            await conn.execute("BEGIN")
            for t, ddl in {**FOUNDATION_DDL, **PHASE6_DDL}.items():
                await conn.execute(ddl)
            await conn.execute("ROLLBACK")
            print("  Idempotency: second CREATE of all tables OK (no error)")
        except Exception as e:  # pragma: no cover
            await conn.execute("ROLLBACK")
            ok = False
            print(f"  Idempotency FAILED: {e}")

        print(f"\nSCHEMA GATE: {'PASS' if ok else 'FAIL'}")
        return 0 if ok else 1
    finally:
        await conn.close()


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
