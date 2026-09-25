"""Reconcile Master Data migrations with the delivered database schema.

The Phase 0 migration drifted from the schema used by the official Master
Data database. This additive repair restores the source-compatible types,
nullability and defaults so an Alembic-built database can accept its backup.

Revision ID: q9r0s1t2u3v4
Revises: q8r9s0t1u2v3
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "q9r0s1t2u3v4"
down_revision: str | None = "q8r9s0t1u2v3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


_JSONB_COLUMNS = {
    "md_audit_events": ("old_value", "new_value", "details"),
    "md_enrichment_tasks": ("evidence",),
    "md_entity_matches": ("match_signals",),
    "md_entity_merge_history": ("source_entity_ids", "details"),
    "md_external_identities": ("sync_metadata",),
    "md_external_systems": ("config",),
    "md_global_companies": ("merged_from_ids", "metadata"),
    "md_global_people": ("metadata",),
    "md_ingestion_batches": ("changes_applied",),
    "md_quality_scores": ("details",),
    "md_sharing_policies": ("shared_categories", "excluded_categories"),
    "md_source_files": ("schema_mapping",),
    "md_source_rows": ("raw_payload", "normalized_payload"),
    "md_tenant_entity_bindings": ("tenant_specific_data",),
}


def upgrade() -> None:
    # JSONB is the persisted Master Data contract (including raw payloads).
    for table, columns in _JSONB_COLUMNS.items():
        for column in columns:
            op.execute(
                f'ALTER TABLE "{table}" ALTER COLUMN "{column}" '
                f'TYPE jsonb USING "{column}"::jsonb'
            )

    # Entity match IDs identify source records and are not necessarily UUIDs.
    op.execute("ALTER TABLE md_entity_matches ALTER COLUMN global_entity_id DROP NOT NULL")
    for column in ("source_a_id", "source_b_id"):
        op.execute(
            f"ALTER TABLE md_entity_matches ALTER COLUMN {column} "
            f"TYPE varchar(255) USING {column}::text"
        )
    op.execute("ALTER TABLE md_entity_matches ALTER COLUMN source_b_id SET NOT NULL")
    op.execute("ALTER TABLE md_entity_matches ALTER COLUMN match_score SET DEFAULT 0.0")
    op.execute(
        "ALTER TABLE md_entity_matches ALTER COLUMN match_signals " "SET DEFAULT '[]'::jsonb"
    )
    op.execute(
        "ALTER TABLE md_entity_matches ALTER COLUMN match_status " "SET DEFAULT 'pending_review'"
    )
    op.execute("ALTER TABLE md_entity_matches ALTER COLUMN review_decision TYPE varchar(64)")

    # Conflicts may precede canonical entity assignment; source IDs are opaque.
    op.execute("ALTER TABLE md_entity_conflicts ALTER COLUMN global_entity_id DROP NOT NULL")
    op.execute("ALTER TABLE md_entity_conflicts ALTER COLUMN field_name TYPE varchar(128)")
    for column in ("source_a_id", "source_b_id"):
        op.execute(
            f"ALTER TABLE md_entity_conflicts ALTER COLUMN {column} "
            f"TYPE varchar(255) USING {column}::text"
        )
    for column in ("source_a_priority", "source_b_priority"):
        op.execute(f"ALTER TABLE md_entity_conflicts ALTER COLUMN {column} SET DEFAULT 0")

    # Preserve JSON evidence and permit system initiated merge-history rows.
    op.execute("ALTER TABLE md_entity_merge_history ALTER COLUMN performed_by DROP NOT NULL")
    op.execute("ALTER TABLE md_entity_merge_history ALTER COLUMN details SET DEFAULT '{}'::jsonb")
    op.execute("ALTER TABLE md_entity_merge_history ALTER COLUMN details SET NOT NULL")
    op.execute(
        "ALTER TABLE md_entity_merge_history ALTER COLUMN source_entity_ids "
        "SET DEFAULT '[]'::jsonb"
    )

    for column in ("sync_metadata",):
        op.execute(
            f"ALTER TABLE md_external_identities ALTER COLUMN {column} " "SET DEFAULT '{}'::jsonb"
        )
    op.execute("ALTER TABLE md_external_systems ALTER COLUMN config SET DEFAULT '{}'::jsonb")
    for table in ("md_global_companies", "md_global_people"):
        op.execute(f"ALTER TABLE {table} ALTER COLUMN confidence_score SET DEFAULT 0.0")
        op.execute(f"ALTER TABLE {table} ALTER COLUMN metadata SET DEFAULT '{{}}'::jsonb")
    op.execute("ALTER TABLE md_legacy_id_mappings ALTER COLUMN confidence SET DEFAULT 1.0")
    for column in (
        "completeness_score",
        "accuracy_score",
        "consistency_score",
        "freshness_score",
        "provenance_score",
        "overall_score",
    ):
        op.execute(f"ALTER TABLE md_quality_scores ALTER COLUMN {column} SET DEFAULT 0.0")
    op.execute("ALTER TABLE md_quality_scores ALTER COLUMN details SET DEFAULT '{}'::jsonb")
    for column in ("shared_categories", "excluded_categories"):
        op.execute(
            f"ALTER TABLE md_sharing_policies ALTER COLUMN {column} " "SET DEFAULT '[]'::jsonb"
        )
    op.execute(
        "ALTER TABLE md_tenant_entity_bindings ALTER COLUMN tenant_specific_data "
        "SET DEFAULT '{}'::jsonb"
    )

    # Fractional authority values and historical rows without a source row are valid.
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN field_name TYPE varchar(128)")
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN source_row_id DROP NOT NULL")
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN observed_at SET DEFAULT now()")
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN evidence_tier TYPE varchar(64)")
    op.execute(
        "ALTER TABLE md_field_provenance ALTER COLUMN authority_score "
        "TYPE double precision USING authority_score::double precision"
    )
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN authority_score SET DEFAULT 0.0")
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN selection_reason TYPE varchar(128)")
    op.execute("ALTER TABLE md_field_provenance ALTER COLUMN selection_reason DROP NOT NULL")

    # Match the official Master Data indexes. The foundation migration's
    # partial unique current-value index contradicts 27,288 groups in the
    # delivered provenance history (34,716 extra current rows), so retaining
    # it would reject real source evidence.
    op.execute("DROP INDEX ix_md_field_prov_unique_current")
    op.create_index(
        "ix_md_entity_matches_pair",
        "md_entity_matches",
        ["source_a_id", "source_b_id"],
        unique=True,
    )
    op.create_index(
        "ix_md_global_companies_slug2",
        "md_global_companies",
        ["slug"],
        unique=True,
        postgresql_where="deleted_at IS NULL",
    )
    op.drop_index("ix_md_quality_entity", table_name="md_quality_scores")
    op.drop_index("ix_md_quality_scored", table_name="md_quality_scores")
    op.create_index(
        "ix_md_quality_scores_entity",
        "md_quality_scores",
        ["global_entity_id", sa.text("scored_at DESC")],
    )


def downgrade() -> None:
    raise RuntimeError(
        "Master Data schema reconciliation is intentionally irreversible; "
        "restoring narrower ID/JSON/numeric types can lose source evidence."
    )
