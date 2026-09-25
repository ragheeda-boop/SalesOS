"""Persist Phase 7 MA-to-company proposals without mutating canonical people.

Revision ID: x7y8z9a0b1c2
Revises: w6x7y8z9a0b1
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "x7y8z9a0b1c2"
down_revision: str | None = "w6x7y8z9a0b1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "md_person_company_link_proposals",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("source_person_key", sa.String(128), nullable=False),
        sa.Column("proposed_company_id", sa.Uuid(), nullable=True),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("match_method", sa.String(96), nullable=False),
        sa.Column("evidence", postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),
        sa.Column("manifest_sha256", sa.String(64), nullable=False),
        sa.Column("reviewer", sa.String(255), nullable=False),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("applied_person_id", sa.Uuid(), nullable=True),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("source_person_key", name="uq_md_person_company_link_proposal_key"),
        if_not_exists=True,
    )
    op.create_index(
        "ix_md_person_company_link_proposals_status",
        "md_person_company_link_proposals",
        ["status"],
        if_not_exists=True,
    )
    op.create_index(
        "ix_md_person_company_link_proposals_company",
        "md_person_company_link_proposals",
        ["proposed_company_id"],
        if_not_exists=True,
    )


def downgrade() -> None:
    raise RuntimeError("Phase 7 proposal history is preserved; downgrade is unsupported.")
