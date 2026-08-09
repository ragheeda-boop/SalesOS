"""ADR-031: activity_attributions — Sales Activity Attribution table.

Revision ID: ec0e98ec106b
Revises: m5b0a1c2d3e4
Create Date: 2026-08-10

Attribution results store: evidence, confidence, provenance, ambiguity.
Shadow mode — writes do not affect scoring or user-visible decisions.
"""
from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

from app.alembic.lib.rls import generate_policy_sql

revision: str = "ec0e98ec106b"
down_revision: str | None = "m5b0a1c2d3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "activity_attributions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False),

        sa.Column("activity_type", sa.String(20), nullable=False),
        sa.Column("activity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("activity_source_table", sa.String(50), nullable=False),

        sa.Column("opportunity_id", sa.String(36), nullable=False),

        sa.Column("resolution_method", sa.String(30), nullable=False),
        sa.Column("resolution_chain", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'[]'::jsonb")),

        sa.Column("evidence", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, default=0),
        sa.Column("confidence_breakdown", postgresql.JSONB, nullable=False,
                  server_default=sa.text("'{}'::jsonb")),

        sa.Column("algorithm_version", sa.String(30), nullable=False),
        sa.Column("resolved_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),

        sa.Column("resolution_state", sa.String(20), nullable=False,
                  server_default="confirmed"),
        sa.Column("alternative_candidates", postgresql.JSONB, nullable=True),

        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now()),
    )

    op.execute(sa.text(
        "ALTER TABLE activity_attributions ADD CONSTRAINT uq_aa_activity_opp "
        "UNIQUE (tenant_id, activity_type, activity_id, opportunity_id)"
    ))

    op.create_index("idx_aa_tenant", "activity_attributions", ["tenant_id"])
    op.create_index("idx_aa_activity", "activity_attributions", ["activity_type", "activity_id"])
    op.create_index("idx_aa_opportunity", "activity_attributions", ["opportunity_id"])
    op.create_index("idx_aa_resolution_state", "activity_attributions",
                    ["tenant_id", "resolution_state"])
    op.create_index("idx_aa_tenant_opp", "activity_attributions",
                    ["tenant_id", "opportunity_id"])

    # RLS
    for stmt in generate_policy_sql("activity_attributions").strip().split(";\n"):
        if stmt.strip():
            op.execute(sa.text(stmt.strip()))


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS tenant_isolation_activity_attributions ON activity_attributions'))
    op.drop_table("activity_attributions")
