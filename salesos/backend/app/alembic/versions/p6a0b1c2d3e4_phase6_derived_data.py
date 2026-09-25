"""Phase 6 derived Master Data schema, previously created out of band.

This revision replaces the `phase6_schema_gate.py` Alembic stamp with tracked
DDL. It creates only derived/history/review-candidate tables and never mutates
canonical Master Data or source evidence.

Revision ID: p6a0b1c2d3e4
Revises: o0p1q2r3s4t5
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "p6a0b1c2d3e4"
down_revision: str | None = "o0p1q2r3s4t5"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "md_identity_classifications",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("classification_version", sa.String(32), nullable=False),
        sa.Column("identity_state", sa.String(40), nullable=False),
        sa.Column("sales_readiness", sa.String(40), nullable=False),
        sa.Column("review_priority", sa.String(4), nullable=False),
        sa.Column("cr_class", sa.String(24), nullable=True),
        sa.Column("has_cr", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_vat", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_unified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("has_real_domain", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "independent_source_count", sa.Integer(), nullable=False, server_default=sa.text("1")
        ),
        sa.Column("source_count", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("conflicts", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column(
            "signals", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "source_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "global_entity_id", "classification_version", name="uq_md_identity_class"
        ),
    )
    op.create_index(
        "ix_md_identity_class_entity", "md_identity_classifications", ["global_entity_id"]
    )
    op.create_index("ix_md_identity_class_state", "md_identity_classifications", ["identity_state"])

    op.create_table(
        "md_review_candidates",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("candidate_type", sa.String(4), nullable=False),
        sa.Column("priority_score", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("reason", sa.String(255), nullable=False),
        sa.Column(
            "evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "source_ids", postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")
        ),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("decision", sa.String(24), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "global_entity_id", "candidate_type", "reason", name="uq_md_review_candidate"
        ),
    )
    op.create_index(
        "ix_md_review_candidate_type", "md_review_candidates", ["candidate_type", "status"]
    )

    op.create_table(
        "md_p0_dispositions",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("conflict_id", sa.Uuid(), nullable=False),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("disposition", sa.String(12), nullable=False),
        sa.Column("reviewer", sa.String(255), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "previous_state",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column(
            "new_state", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "source_records",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("conflict_id", "reviewer", name="uq_md_p0_disposition"),
    )
    op.create_index("ix_md_p0_disposition_conflict", "md_p0_dispositions", ["conflict_id"])

    op.create_table(
        "md_industry_normalization",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("raw_industry", sa.Text(), nullable=False),
        sa.Column("normalized_industry", sa.String(255), nullable=True),
        sa.Column("industry_code", sa.String(64), nullable=True),
        sa.Column("normalization_method", sa.String(64), nullable=False),
        sa.Column("source_row_id", sa.Uuid(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "global_entity_id", "raw_industry", "normalization_method", name="uq_md_industry_norm"
        ),
    )
    op.create_index(
        "ix_md_industry_norm_entity",
        "md_industry_normalization",
        ["global_entity_id", "is_current"],
    )

    op.create_table(
        "md_contact_relationships",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("person_global_id", sa.Uuid(), nullable=False),
        sa.Column("company_global_id", sa.Uuid(), nullable=False),
        sa.Column(
            "relationship_type", sa.String(32), nullable=False, server_default=sa.text("'account'")
        ),
        sa.Column("status", sa.String(16), nullable=False, server_default=sa.text("'INFERRED'")),
        sa.Column("linking_basis", sa.String(64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("source_id", sa.String(64), nullable=True),
        sa.Column(
            "observed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint(
            "person_global_id", "company_global_id", "linking_basis", name="uq_md_contact_rel"
        ),
    )
    op.create_index("ix_md_contact_rel_person", "md_contact_relationships", ["person_global_id"])
    op.create_index("ix_md_contact_rel_company", "md_contact_relationships", ["company_global_id"])

    op.create_table(
        "md_quality_score_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("calc_version", sa.String(32), nullable=False),
        sa.Column("completeness_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("accuracy_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("consistency_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("freshness_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("provenance_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column("overall_score", sa.Float(), nullable=False, server_default=sa.text("0.0")),
        sa.Column(
            "evidence_basis",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("previous_version", sa.String(32), nullable=True),
        sa.Column("previous_overall", sa.Float(), nullable=True),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("global_entity_id", "calc_version", name="uq_md_quality_hist"),
    )
    op.create_index("ix_md_quality_hist_entity", "md_quality_score_history", ["global_entity_id"])

    op.create_table(
        "md_sales_readiness_history",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("global_entity_id", sa.Uuid(), nullable=False),
        sa.Column("calc_version", sa.String(32), nullable=False),
        sa.Column("sales_readiness", sa.String(40), nullable=False),
        sa.Column("identity_state", sa.String(40), nullable=False),
        sa.Column(
            "basis", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("previous_version", sa.String(32), nullable=True),
        sa.Column("previous_readiness", sa.String(40), nullable=True),
        sa.Column(
            "computed_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("global_entity_id", "calc_version", name="uq_md_sales_readiness"),
    )
    op.create_index(
        "ix_md_sales_readiness_entity", "md_sales_readiness_history", ["global_entity_id"]
    )


def downgrade() -> None:
    raise RuntimeError("Phase 6 derived and review history is preserved; downgrade is unsupported.")
