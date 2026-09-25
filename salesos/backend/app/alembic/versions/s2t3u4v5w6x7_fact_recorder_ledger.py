"""Add tenant-scoped evidence and canonical fact proposal ledger.

Revision ID: s2t3u4v5w6x7
Revises: r1s2t3u4v5w6
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "s2t3u4v5w6x7"
down_revision: str | None = "r1s2t3u4v5w6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_TENANT_TABLES = (
    "evidence_records",
    "canonical_facts",
    "fact_evidence",
    "canonical_fact_events",
)


def _apply_tenant_rls(table: str) -> None:
    for statement in generate_policy_sql(table).strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement))


def upgrade() -> None:
    op.create_table(
        "evidence_records",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("source_domain", sa.String(64), nullable=False),
        sa.Column("source_type", sa.String(64), nullable=False),
        sa.Column("source_id", sa.String(255)),
        sa.Column("source_name", sa.String(255)),
        sa.Column("evidence_kind", sa.String(100), nullable=False),
        sa.Column("description", sa.Text()),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column(
            "data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column("evidence_hash", sa.String(64), nullable=False),
        sa.Column("observed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("id", "tenant_id", name="uq_evidence_records_id_tenant"),
        sa.UniqueConstraint("tenant_id", "evidence_hash", name="uq_evidence_records_tenant_hash"),
        sa.CheckConstraint(
            "confidence >= 0 AND confidence <= 1", name="ck_evidence_records_confidence"
        ),
    )
    op.create_index(
        "ix_evidence_records_tenant_observed", "evidence_records", ["tenant_id", "observed_at"]
    )

    op.create_table(
        "canonical_facts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("subject_type", sa.String(16), nullable=False),
        sa.Column("subject_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("field_name", sa.String(100), nullable=False),
        sa.Column("proposed_value", postgresql.JSONB(), nullable=False),
        sa.Column("value_hash", sa.String(64), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="PROPOSED"),
        sa.Column("evidence_band", sa.String(20), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("decision_reason", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=False),
        sa.Column("request_fingerprint", sa.String(64), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(128)),
        sa.Column("reviewer_id", sa.String(128)),
        sa.Column("reviewed_at", sa.DateTime(timezone=True)),
        sa.Column("applied_at", sa.DateTime(timezone=True)),
        sa.Column("supersedes_fact_id", postgresql.UUID(as_uuid=True)),
        sa.Column(
            "evidence_snapshot",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'[]'::jsonb"),
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("id", "tenant_id", name="uq_canonical_facts_id_tenant"),
        sa.UniqueConstraint("tenant_id", "idempotency_key", name="uq_canonical_facts_idempotency"),
        sa.CheckConstraint(
            "subject_type IN ('company', 'contact')", name="ck_canonical_facts_subject_type"
        ),
        sa.CheckConstraint(
            "status IN ('PROPOSED', 'APPROVED', 'REJECTED', 'DISMISSED', 'APPLIED', 'SUPERSEDED', 'STALE')",
            name="ck_canonical_facts_status",
        ),
        sa.CheckConstraint("score >= 0 AND score <= 1", name="ck_canonical_facts_score"),
        sa.ForeignKeyConstraint(
            ["supersedes_fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            name="fk_canonical_facts_supersedes_tenant",
        ),
    )
    op.create_index(
        "ix_canonical_facts_tenant_subject",
        "canonical_facts",
        ["tenant_id", "subject_type", "subject_id"],
    )
    op.create_index("ix_canonical_facts_tenant_status", "canonical_facts", ["tenant_id", "status"])
    op.create_index(
        "uq_canonical_facts_open_value",
        "canonical_facts",
        ["tenant_id", "subject_type", "subject_id", "field_name", "value_hash"],
        unique=True,
        postgresql_where=sa.text("status = 'PROPOSED'"),
    )
    op.create_index(
        "uq_canonical_facts_dismissed_value",
        "canonical_facts",
        ["tenant_id", "subject_type", "subject_id", "field_name", "value_hash"],
        unique=True,
        postgresql_where=sa.text("status = 'DISMISSED'"),
    )

    op.create_table(
        "fact_evidence",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("evidence_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("relation", sa.String(24), nullable=False, server_default="SUPPORTS"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            ondelete="CASCADE",
            name="fk_fact_evidence_fact_tenant",
        ),
        sa.ForeignKeyConstraint(
            ["evidence_id", "tenant_id"],
            ["evidence_records.id", "evidence_records.tenant_id"],
            ondelete="CASCADE",
            name="fk_fact_evidence_evidence_tenant",
        ),
        sa.UniqueConstraint(
            "tenant_id", "fact_id", "evidence_id", name="uq_fact_evidence_tenant_fact_evidence"
        ),
    )
    op.create_index(
        "ix_fact_evidence_tenant_evidence", "fact_evidence", ["tenant_id", "evidence_id"]
    )

    op.create_table(
        "canonical_fact_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("fact_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(32), nullable=False),
        sa.Column("from_status", sa.String(20)),
        sa.Column("to_status", sa.String(20), nullable=False),
        sa.Column("actor_type", sa.String(32), nullable=False),
        sa.Column("actor_id", sa.String(128)),
        sa.Column("reason", sa.Text()),
        sa.Column(
            "event_data", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")
        ),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.ForeignKeyConstraint(
            ["fact_id", "tenant_id"],
            ["canonical_facts.id", "canonical_facts.tenant_id"],
            ondelete="CASCADE",
            name="fk_canonical_fact_events_fact_tenant",
        ),
    )
    op.create_index(
        "ix_canonical_fact_events_tenant_fact",
        "canonical_fact_events",
        ["tenant_id", "fact_id", "created_at"],
    )

    for table in _TENANT_TABLES:
        _apply_tenant_rls(table)


def downgrade() -> None:
    for table in reversed(_TENANT_TABLES):
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
    op.drop_table("canonical_fact_events")
    op.drop_table("fact_evidence")
    op.drop_table("canonical_facts")
    op.drop_table("evidence_records")
