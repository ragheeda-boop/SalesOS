"""Phase 0: Master Data Foundation — 22 tables for Global Master Data platform.

Creates the complete schema for the Master Data & Data Intelligence Layer:
- 14 global tables (NO RLS — application-layer ACL)
- 8 tenant-scoped tables (RLS via existing patterns)

Global tables: md_global_companies, md_global_people, md_legacy_id_mappings,
  md_entity_matches, md_entity_conflicts, md_entity_merge_history,
  md_external_systems, md_external_identities, md_quality_scores,
  md_quality_issues, md_enrichment_tasks, md_enrichment_evidence,
  md_field_provenance, md_audit_events

Tenant tables: md_source_files, md_source_rows, md_source_values,
  md_ingestion_batches, md_tenant_entity_bindings, md_tenant_entity_attributes,
  md_sharing_policies, md_sharing_consents

Source data immutability: md_source_rows.raw_payload and md_source_values.original_value
  are NEVER modified after ingestion.

Revision: i3j4k5l6m7n8 + 1 = phase0_master_data_foundation
Revises: m5b0a1c2d3e4 (latest)
Create Date: 2026-08-28
"""
import sqlalchemy as sa
from alembic import op

revision = "j4k5l6m7n8o9"
down_revision = "m5b0a1c2d3e4"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ════════════════════════════════════════════════════════════════════════
    # GLOBAL TABLES (NO RLS)
    # ════════════════════════════════════════════════════════════════════════

    # ── 2.5 md_global_companies ──────────────────────────────────────────
    op.create_table(
        "md_global_companies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("canonical_name", sa.String(512), nullable=False),
        sa.Column("canonical_name_ar", sa.String(512), nullable=True),
        sa.Column("canonical_name_en", sa.String(512), nullable=True),
        sa.Column("cr_number", sa.String(50), nullable=True),
        sa.Column("vat_number", sa.String(50), nullable=True),
        sa.Column("unified_national_number", sa.String(50), nullable=True),
        sa.Column("domain", sa.String(255), nullable=True),
        sa.Column("website", sa.String(512), nullable=True),
        sa.Column("city", sa.String(100), nullable=True),
        sa.Column("region", sa.String(100), nullable=True),
        sa.Column("country", sa.String(100), nullable=False, server_default="Saudi Arabia"),
        sa.Column("industry", sa.String(255), nullable=True),
        sa.Column("legal_entity_type", sa.String(32), nullable=False, server_default="company"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("latitude", sa.Float(), nullable=True),
        sa.Column("longitude", sa.Float(), nullable=True),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("merged_from_ids", sa.JSON(), nullable=True),
        sa.Column("merged_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("split_from_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_md_global_companies_slug", "md_global_companies", ["slug"], unique=True)
    op.create_index(
        "ix_md_global_companies_cr",
        "md_global_companies",
        ["cr_number"],
        unique=False,
        postgresql_where="cr_number IS NOT NULL AND cr_number != ''",
    )
    op.create_index(
        "ix_md_global_companies_domain",
        "md_global_companies",
        ["domain"],
        unique=False,
        postgresql_where="domain IS NOT NULL",
    )
    op.create_index("ix_md_global_companies_name", "md_global_companies", ["canonical_name"])
    op.create_index("ix_md_global_companies_status", "md_global_companies", ["status"])

    # ── 2.6 md_global_people ─────────────────────────────────────────────
    op.create_table(
        "md_global_people",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("slug", sa.String(64), nullable=False),
        sa.Column("canonical_name", sa.String(512), nullable=False),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("company_global_id", sa.Uuid(), nullable=True),
        sa.Column("job_title", sa.String(255), nullable=True),
        sa.Column("linkedin_url", sa.String(512), nullable=True),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_md_global_people_slug", "md_global_people", ["slug"], unique=True)
    op.create_index(
        "ix_md_global_people_email",
        "md_global_people",
        ["email"],
        unique=False,
        postgresql_where="email IS NOT NULL",
    )
    op.create_index("ix_md_global_people_company", "md_global_people", ["company_global_id"])
    op.create_index("ix_md_global_people_name", "md_global_people", ["canonical_name"])

    # ── 2.7 md_legacy_id_mappings ────────────────────────────────────────
    op.create_table(
        "md_legacy_id_mappings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("legacy_id_type", sa.String(32), nullable=False),
        sa.Column("legacy_id", sa.String(255), nullable=False),
        sa.Column("global_entity_type", sa.String(32), nullable=False),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_md_legacy_id_lookup",
        "md_legacy_id_mappings",
        ["legacy_id_type", "legacy_id"],
        unique=True,
    )
    op.create_index(
        "ix_md_legacy_id_global",
        "md_legacy_id_mappings",
        ["global_entity_type", "global_entity_id"],
    )

    # ── 2.8 md_entity_matches ────────────────────────────────────────────
    op.create_table(
        "md_entity_matches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("source_a_id", sa.Uuid(), nullable=False),
        sa.Column("source_b_id", sa.Uuid(), nullable=True),
        sa.Column("match_score", sa.Float(), nullable=False),
        sa.Column("match_method", sa.String(64), nullable=False),
        sa.Column("match_signals", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("match_status", sa.String(32), nullable=False),
        sa.Column("reviewed_by", sa.Uuid(), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_decision", sa.String(32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_md_entity_matches_entity", "md_entity_matches", ["global_entity_id"])
    op.create_index("ix_md_entity_matches_status", "md_entity_matches", ["match_status"])
    op.create_index("ix_md_entity_matches_source_a", "md_entity_matches", ["source_a_id"])
    op.create_index("ix_md_entity_matches_source_b", "md_entity_matches", ["source_b_id"])

    # ── 2.9 md_entity_conflicts ──────────────────────────────────────────
    op.create_table(
        "md_entity_conflicts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("value_a", sa.Text(), nullable=True),
        sa.Column("source_a_id", sa.Uuid(), nullable=True),
        sa.Column("source_a_priority", sa.Integer(), nullable=True),
        sa.Column("value_b", sa.Text(), nullable=True),
        sa.Column("source_b_id", sa.Uuid(), nullable=True),
        sa.Column("source_b_priority", sa.Integer(), nullable=True),
        sa.Column("is_government_id", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("veto_enabled", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("resolution", sa.String(32), nullable=False, server_default="open"),
        sa.Column("resolved_value", sa.Text(), nullable=True),
        sa.Column("resolved_by", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_entity_conflicts_entity",
        "md_entity_conflicts",
        ["global_entity_id", "resolution"],
    )
    op.create_index("ix_md_entity_conflicts_field", "md_entity_conflicts", ["field_name"])

    # ── 2.10 md_entity_merge_history ─────────────────────────────────────
    op.create_table(
        "md_entity_merge_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("operation", sa.String(32), nullable=False),
        sa.Column("target_entity_id", sa.Uuid(), nullable=False),
        sa.Column("source_entity_ids", sa.JSON(), nullable=False),
        sa.Column("match_score", sa.Float(), nullable=True),
        sa.Column("match_method", sa.String(64), nullable=True),
        sa.Column("performed_by", sa.Uuid(), nullable=False),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("rollback_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
    )
    op.create_index("ix_md_merge_history_target", "md_entity_merge_history", ["target_entity_id"])
    op.create_index(
        "ix_md_merge_history_performed",
        "md_entity_merge_history",
        [sa.text("performed_at DESC")],
    )

    # ── 2.13 md_external_systems ─────────────────────────────────────────
    op.create_table(
        "md_external_systems",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("system_key", sa.String(64), nullable=False),
        sa.Column("display_name", sa.String(128), nullable=False),
        sa.Column("supports_incremental", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("config", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_external_systems_key",
        "md_external_systems",
        ["system_key"],
        unique=True,
    )

    # ── 2.14 md_external_identities ──────────────────────────────────────
    op.create_table(
        "md_external_identities",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("system_key", sa.String(64), nullable=False),
        sa.Column("object_type", sa.String(64), nullable=False),
        sa.Column("external_id", sa.String(255), nullable=False),
        sa.Column("external_name", sa.String(512), nullable=True),
        sa.Column("external_url", sa.String(1024), nullable=True),
        sa.Column("sync_status", sa.String(32), nullable=False, server_default="synced"),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sync_metadata", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_external_identities_unique",
        "md_external_identities",
        ["tenant_id", "system_key", "object_type", "external_id"],
        unique=True,
    )
    op.create_index("ix_md_external_global", "md_external_identities", ["global_entity_id"])
    op.create_index(
        "ix_md_external_tenant_system",
        "md_external_identities",
        ["tenant_id", "system_key"],
    )

    # ── 2.15 md_quality_scores ───────────────────────────────────────────
    op.create_table(
        "md_quality_scores",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("accuracy_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("consistency_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("provenance_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("scored_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("details", sa.JSON(), nullable=False, server_default="{}"),
    )
    op.create_index("ix_md_quality_entity", "md_quality_scores", ["global_entity_id"])
    op.create_index(
        "ix_md_quality_scored",
        "md_quality_scores",
        [sa.text("scored_at DESC")],
    )

    # ── 2.16 md_quality_issues ───────────────────────────────────────────
    op.create_table(
        "md_quality_issues",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("issue_type", sa.String(64), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("status", sa.String(32), nullable=False, server_default="open"),
        sa.Column("assigned_to", sa.Uuid(), nullable=True),
        sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_quality_issues_entity",
        "md_quality_issues",
        ["global_entity_id", "status"],
    )
    op.create_index(
        "ix_md_quality_issues_type",
        "md_quality_issues",
        ["issue_type", "status"],
    )
    op.create_index(
        "ix_md_quality_issues_severity",
        "md_quality_issues",
        ["severity", "status"],
    )

    # ── 2.17 md_enrichment_tasks ─────────────────────────────────────────
    op.create_table(
        "md_enrichment_tasks",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("current_value", sa.Text(), nullable=True),
        sa.Column("missing_since", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="100"),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("enrichment_method", sa.String(64), nullable=True),
        sa.Column("proposed_value", sa.Text(), nullable=True),
        sa.Column("proposed_confidence", sa.Float(), nullable=True),
        sa.Column("evidence", sa.JSON(), nullable=True),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_enrichment_entity",
        "md_enrichment_tasks",
        ["global_entity_id", "status"],
    )
    op.create_index(
        "ix_md_enrichment_priority",
        "md_enrichment_tasks",
        ["priority", "status"],
        postgresql_where="status = 'pending'",
    )

    # ── 2.18 md_enrichment_evidence ──────────────────────────────────────
    op.create_table(
        "md_enrichment_evidence",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("task_id", sa.Uuid(), nullable=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("value", sa.Text(), nullable=False),
        sa.Column("source_type", sa.String(32), nullable=False),
        sa.Column("source_detail", sa.Text(), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="unverified"),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_enrichment_evidence_entity",
        "md_enrichment_evidence",
        ["global_entity_id", "field_name"],
    )
    op.create_index("ix_md_enrichment_evidence_task", "md_enrichment_evidence", ["task_id"])

    # ── 2.21 md_audit_events ─────────────────────────────────────────────
    op.create_table(
        "md_audit_events",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=True),
        sa.Column("event_type", sa.String(64), nullable=False),
        sa.Column("actor_id", sa.Uuid(), nullable=True),
        sa.Column("actor_type", sa.String(32), nullable=False, server_default="user"),
        sa.Column("old_value", sa.JSON(), nullable=True),
        sa.Column("new_value", sa.JSON(), nullable=True),
        sa.Column("source_record_id", sa.Uuid(), nullable=True),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("performed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_audit_entity",
        "md_audit_events",
        [sa.text("global_entity_id, performed_at DESC")],
    )
    op.create_index(
        "ix_md_audit_type",
        "md_audit_events",
        [sa.text("event_type, performed_at DESC")],
    )
    op.create_index("ix_md_audit_batch", "md_audit_events", ["import_batch_id"])
    op.create_index(
        "ix_md_audit_performed",
        "md_audit_events",
        [sa.text("performed_at DESC")],
    )

    # ── 2.22 md_field_provenance ─────────────────────────────────────────
    op.create_table(
        "md_field_provenance",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("field_value", sa.Text(), nullable=False),
        sa.Column("source_row_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=True),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("evidence_tier", sa.String(32), nullable=False),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="unverified"),
        sa.Column("verified_by", sa.Uuid(), nullable=True),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("authority_score", sa.Integer(), nullable=False),
        sa.Column("selection_reason", sa.String(64), nullable=False),
        sa.Column("conflict_status", sa.String(32), nullable=False, server_default="none"),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("superseded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_md_field_prov_entity", "md_field_provenance", ["global_entity_id", "field_name"])
    op.create_index("ix_md_field_prov_source", "md_field_provenance", ["source_row_id"])
    op.create_index(
        "ix_md_field_prov_current",
        "md_field_provenance",
        ["global_entity_id", "field_name"],
        postgresql_where="is_current = true",
    )
    # Partial unique: one current value per field per entity
    op.create_index(
        "ix_md_field_prov_unique_current",
        "md_field_provenance",
        ["global_entity_id", "field_name"],
        unique=True,
        postgresql_where="is_current = true",
    )

    # ══════════════════════════════════════════════════════════════════════
    # TENANT-SCOPED TABLES (WITH RLS)
    # ══════════════════════════════════════════════════════════════════════

    # ── 2.1 md_source_files ──────────────────────────────────────────────
    op.create_table(
        "md_source_files",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("filename", sa.String(512), nullable=False),
        sa.Column("storage_path", sa.String(1024), nullable=False),
        sa.Column("file_hash_sha256", sa.String(64), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(128), nullable=False),
        sa.Column("sheet_count", sa.Integer(), nullable=False),
        sa.Column("total_rows", sa.Integer(), nullable=False),
        sa.Column("source_system", sa.String(64), nullable=False),
        sa.Column("schema_mapping", sa.JSON(), nullable=True),
        sa.Column("uploaded_by", sa.Uuid(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("status", sa.String(32), nullable=False, server_default="uploaded"),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_md_source_files_tenant",
        "md_source_files",
        [sa.text("tenant_id, uploaded_at DESC")],
    )
    op.create_index("ix_md_source_files_hash", "md_source_files", ["file_hash_sha256"])
    op.create_index("ix_md_source_files_source_system", "md_source_files", ["source_system"])

    # ── 2.2 md_source_rows ───────────────────────────────────────────────
    op.create_table(
        "md_source_rows",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=False),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("source_record_id", sa.String(255), nullable=False),
        sa.Column("row_number", sa.Integer(), nullable=False),
        sa.Column("sheet_name", sa.String(255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=True),
        sa.Column("entity_type", sa.String(32), nullable=False, server_default="company"),
        sa.Column("global_entity_id", sa.Uuid(), nullable=True),
        sa.Column("resolution_status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("resolution_confidence", sa.Float(), nullable=True),
        sa.Column("resolution_method", sa.String(64), nullable=True),
        sa.Column("import_batch_id", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_md_source_rows_source",
        "md_source_rows",
        ["source_id", "source_record_id"],
        unique=True,
    )
    op.create_index(
        "ix_md_source_rows_file",
        "md_source_rows",
        ["source_file_id", "row_number"],
    )
    op.create_index("ix_md_source_rows_global_entity", "md_source_rows", ["global_entity_id"])
    op.create_index("ix_md_source_rows_batch", "md_source_rows", ["import_batch_id"])
    op.create_index(
        "ix_md_source_rows_tenant",
        "md_source_rows",
        [sa.text("tenant_id, created_at DESC")],
    )

    # ── 2.3 md_source_values ─────────────────────────────────────────────
    op.create_table(
        "md_source_values",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_row_id", sa.Uuid(), nullable=False),
        sa.Column("field_name", sa.String(255), nullable=False),
        sa.Column("original_value", sa.Text(), nullable=True),
        sa.Column("normalized_value", sa.Text(), nullable=True),
        sa.Column("canonical_field", sa.String(255), nullable=True),
        sa.Column("confidence", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_md_source_values_row", "md_source_values", ["source_row_id"])
    op.create_index("ix_md_source_values_field", "md_source_values", ["canonical_field"])

    # ── 2.4 md_ingestion_batches ─────────────────────────────────────────
    op.create_table(
        "md_ingestion_batches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("source_file_id", sa.Uuid(), nullable=True),
        sa.Column("import_type", sa.String(32), nullable=False),
        sa.Column("status", sa.String(32), nullable=False, server_default="pending"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("imported_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("matched_entities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("new_entities", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("conflict_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("review_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("changes_applied", sa.JSON(), nullable=True),
        sa.Column("rollback_available", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("rolled_back_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("performed_by", sa.Uuid(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_ingestion_batches_tenant",
        "md_ingestion_batches",
        [sa.text("tenant_id, started_at DESC")],
    )
    op.create_index("ix_md_ingestion_batches_status", "md_ingestion_batches", ["status"])

    # ── 2.11 md_tenant_entity_bindings ───────────────────────────────────
    op.create_table(
        "md_tenant_entity_bindings",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("relationship_type", sa.String(32), nullable=False, server_default="account"),
        sa.Column("status", sa.String(32), nullable=False, server_default="active"),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("tenant_specific_name", sa.String(512), nullable=True),
        sa.Column("tenant_specific_data", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("source_binding_id", sa.Uuid(), nullable=True),
        sa.Column("bound_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_bindings_unique",
        "md_tenant_entity_bindings",
        ["tenant_id", "global_entity_id"],
        unique=True,
    )
    op.create_index(
        "ix_md_bindings_tenant",
        "md_tenant_entity_bindings",
        ["tenant_id", "status"],
    )
    op.create_index("ix_md_bindings_global", "md_tenant_entity_bindings", ["global_entity_id"])
    op.create_index("ix_md_bindings_relationship", "md_tenant_entity_bindings", ["relationship_type"])

    # ── 2.12 md_tenant_entity_attributes ─────────────────────────────────
    op.create_table(
        "md_tenant_entity_attributes",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("binding_id", sa.Uuid(), nullable=False),
        sa.Column("attribute_name", sa.String(255), nullable=False),
        sa.Column("attribute_value", sa.Text(), nullable=True),
        sa.Column("source", sa.String(64), nullable=False, server_default="manual"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_attributes_unique",
        "md_tenant_entity_attributes",
        ["binding_id", "attribute_name"],
        unique=True,
    )

    # ── 2.19 md_sharing_policies ─────────────────────────────────────────
    op.create_table(
        "md_sharing_policies",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("policy_name", sa.String(255), nullable=False),
        sa.Column("policy_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("shared_categories", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("excluded_categories", sa.JSON(), nullable=False, server_default="[]"),
        sa.Column("effective_from", sa.DateTime(timezone=True), nullable=False),
        sa.Column("effective_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_by", sa.Uuid(), nullable=False),
        sa.Column("approved_by", sa.Uuid(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_sharing_policies_tenant",
        "md_sharing_policies",
        ["tenant_id", "is_active"],
    )

    # ── 2.20 md_sharing_consents ─────────────────────────────────────────
    op.create_table(
        "md_sharing_consents",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("tenant_id", sa.Uuid(), nullable=False),
        sa.Column("policy_id", sa.Uuid(), nullable=False),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("consent_status", sa.String(32), nullable=False, server_default="granted"),
        sa.Column("consented_by", sa.Uuid(), nullable=False),
        sa.Column("consented_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index(
        "ix_md_sharing_consents_tenant",
        "md_sharing_consents",
        ["tenant_id", "consent_status"],
    )
    op.create_index("ix_md_sharing_consents_entity", "md_sharing_consents", ["global_entity_id"])

    # ══════════════════════════════════════════════════════════════════════
    # RLS POLICIES (tenant-scoped tables only)
    # ══════════════════════════════════════════════════════════════════════

    _SESSION_VAR = "app.tenant_id"
    _RLS_TABLES = [
        "md_source_files",
        "md_source_rows",
        "md_ingestion_batches",
        "md_tenant_entity_bindings",
        "md_sharing_policies",
        "md_sharing_consents",
        "md_external_identities",
    ]
    for table in _RLS_TABLES:
        op.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY')
        op.execute(
            f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'
        )
        op.execute(
            f'CREATE POLICY "tenant_isolation_{table}" ON "{table}" '
            f"FOR ALL "
            f"USING (tenant_id::text = current_setting('{_SESSION_VAR}', true)) "
            f"WITH CHECK (tenant_id::text = current_setting('{_SESSION_VAR}', true))"
        )

    # md_source_values: FK-based RLS via parent md_source_rows
    op.execute('ALTER TABLE "md_source_values" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "md_source_values" FORCE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS "tenant_isolation_md_source_values" ON "md_source_values"')
    op.execute(
        'CREATE POLICY "tenant_isolation_md_source_values" ON "md_source_values" '
        "FOR ALL "
        "USING (EXISTS ("
        '  SELECT 1 FROM "md_source_rows" sr '
        "  WHERE sr.id = md_source_values.source_row_id "
        "  AND sr.tenant_id::text = current_setting('{sess}', true)"
        ")) "
        "WITH CHECK (EXISTS ("
        '  SELECT 1 FROM "md_source_rows" sr '
        "  WHERE sr.id = md_source_values.source_row_id "
        "  AND sr.tenant_id::text = current_setting('{sess}', true)"
        "))".format(sess=_SESSION_VAR)
    )

    # Source data is append-only. The only operational updates permitted are
    # file status and the derived global-entity linkage on a source row.
    op.execute("""
        CREATE OR REPLACE FUNCTION md_guard_source_immutability()
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
        $$ LANGUAGE plpgsql
    """)
    for source_table in ("md_source_files", "md_source_rows", "md_source_values"):
        op.execute(f'DROP TRIGGER IF EXISTS "trg_{source_table}_immutable" ON "{source_table}"')
        op.execute(
            f'CREATE TRIGGER "trg_{source_table}_immutable" '
            f'BEFORE UPDATE OR DELETE ON "{source_table}" '
            "FOR EACH ROW EXECUTE FUNCTION md_guard_source_immutability()"
        )

    # 02-app-role.sql grants CRUD defaults before migrations run. Revoke broad
    # mutation rights from source evidence while preserving the reviewed paths.
    op.execute("""
        DO $$ BEGIN
            IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN
                REVOKE UPDATE, DELETE ON TABLE md_source_files FROM salesos_app;
                GRANT UPDATE (status) ON TABLE md_source_files TO salesos_app;
                REVOKE UPDATE, DELETE ON TABLE md_source_rows FROM salesos_app;
                GRANT UPDATE (global_entity_id) ON TABLE md_source_rows TO salesos_app;
                REVOKE UPDATE, DELETE ON TABLE md_source_values FROM salesos_app;
            END IF;
        END $$
    """)

    # md_tenant_entity_attributes: FK-based RLS via parent md_tenant_entity_bindings
    op.execute('ALTER TABLE "md_tenant_entity_attributes" ENABLE ROW LEVEL SECURITY')
    op.execute('ALTER TABLE "md_tenant_entity_attributes" FORCE ROW LEVEL SECURITY')
    op.execute('DROP POLICY IF EXISTS "tenant_isolation_md_tenant_entity_attributes" ON "md_tenant_entity_attributes"')
    op.execute(
        'CREATE POLICY "tenant_isolation_md_tenant_entity_attributes" ON "md_tenant_entity_attributes" '
        "FOR ALL "
        "USING (EXISTS ("
        '  SELECT 1 FROM "md_tenant_entity_bindings" b '
        "  WHERE b.id = md_tenant_entity_attributes.binding_id "
        "  AND b.tenant_id::text = current_setting('{sess}', true)"
        ")) "
        "WITH CHECK (EXISTS ("
        '  SELECT 1 FROM "md_tenant_entity_bindings" b '
        "  WHERE b.id = md_tenant_entity_attributes.binding_id "
        "  AND b.tenant_id::text = current_setting('{sess}', true)"
        "))".format(sess=_SESSION_VAR)
    )


def downgrade() -> None:
    for source_table in ("md_source_files", "md_source_rows", "md_source_values"):
        op.execute(f'DROP TRIGGER IF EXISTS "trg_{source_table}_immutable" ON "{source_table}"')
    op.execute("DROP FUNCTION IF EXISTS md_guard_source_immutability()")
    # Drop tenant-scoped tables first (children before parents)
    for table in [
        "md_tenant_entity_attributes",
        "md_sharing_consents",
        "md_sharing_policies",
        "md_tenant_entity_bindings",
        "md_source_values",
        "md_source_rows",
        "md_source_files",
        "md_ingestion_batches",
        "md_external_identities",
    ]:
        op.execute(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"')
        op.execute(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY')
        op.execute(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY')
        op.drop_table(table)

    # Drop global tables (children before parents)
    for table in [
        "md_field_provenance",
        "md_audit_events",
        "md_enrichment_evidence",
        "md_enrichment_tasks",
        "md_quality_issues",
        "md_quality_scores",
        "md_external_systems",
        "md_entity_merge_history",
        "md_entity_conflicts",
        "md_entity_matches",
        "md_legacy_id_mappings",
        "md_global_people",
        "md_global_companies",
    ]:
        op.drop_table(table)
