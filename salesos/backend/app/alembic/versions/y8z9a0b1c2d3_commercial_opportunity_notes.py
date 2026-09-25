"""Persist tenant-scoped, immutable commercial opportunity notes.

Revision ID: y8z9a0b1c2d3
Revises: x7y8z9a0b1c2
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql

revision: str = "y8z9a0b1c2d3"
down_revision: str | None = "x7y8z9a0b1c2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "commercial_opportunity_notes",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column(
            "opportunity_id",
            sa.String(36),
            sa.ForeignKey("commercial_opportunities.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("author_id", sa.String(36), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("idempotency_key", sa.String(128), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint(
            "tenant_id",
            "opportunity_id",
            "idempotency_key",
            name="uq_commercial_opp_note_idempotency",
        ),
    )
    op.create_index(
        "ix_commercial_opp_notes_tenant_opportunity_created",
        "commercial_opportunity_notes",
        ["tenant_id", "opportunity_id", "created_at"],
    )
    for statement in generate_policy_sql("commercial_opportunity_notes").strip().split(";\n"):
        if statement.strip():
            op.execute(sa.text(statement.strip()))
    op.execute(sa.text("REVOKE ALL ON commercial_opportunity_notes FROM PUBLIC"))
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') "
            "THEN GRANT SELECT, INSERT ON commercial_opportunity_notes TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(sa.text('DROP POLICY IF EXISTS "tenant_isolation_commercial_opportunity_notes" ON "commercial_opportunity_notes"'))
    op.execute(sa.text('ALTER TABLE "commercial_opportunity_notes" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text('ALTER TABLE "commercial_opportunity_notes" DISABLE ROW LEVEL SECURITY'))
    op.drop_index("ix_commercial_opp_notes_tenant_opportunity_created", table_name="commercial_opportunity_notes")
    op.drop_table("commercial_opportunity_notes")
