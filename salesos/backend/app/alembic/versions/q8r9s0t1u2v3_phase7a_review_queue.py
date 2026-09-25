"""Phase 7-A review queue schema, previously created out of band.

This records reviewer decisions only; it does not open Phase 7 processing or
promote canonical entities.

Revision ID: q8r9s0t1u2v3
Revises: q7r8s9t0u1v2
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "q8r9s0t1u2v3"
down_revision: str | None = "q7r8s9t0u1v2"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "md_review_queue_state",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("queue_type", sa.String(32), nullable=False),
        sa.Column("subject_key", sa.String(128), nullable=False),
        sa.Column("global_company_id", sa.Uuid(), nullable=True),
        sa.Column("global_company_id_b", sa.Uuid(), nullable=True),
        sa.Column(
            "evidence_ref",
            postgresql.JSONB(),
            nullable=False,
            server_default=sa.text("'{}'::jsonb"),
        ),
        sa.Column("status", sa.String(24), nullable=False, server_default=sa.text("'pending'")),
        sa.Column("disposition", sa.String(32), nullable=True),
        sa.Column("reviewer", sa.String(255), nullable=True),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()
        ),
        sa.UniqueConstraint("queue_type", "subject_key", name="uq_md_review_queue_state"),
    )
    op.create_index(
        "ix_md_review_queue_state_qtype", "md_review_queue_state", ["queue_type", "status"]
    )
    op.create_index(
        "ix_md_review_queue_state_company", "md_review_queue_state", ["global_company_id"]
    )
    op.create_index(
        "ix_md_review_queue_state_company_b", "md_review_queue_state", ["global_company_id_b"]
    )


def downgrade() -> None:
    raise RuntimeError("Phase 7-A review decisions are preserved; downgrade is unsupported.")
