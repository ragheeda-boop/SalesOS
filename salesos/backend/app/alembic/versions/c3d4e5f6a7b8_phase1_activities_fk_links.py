"""Phase 1 Product Core — Activities FK links + Reviews audit trail.

Adds:
  - commercial_activity_sessions.company_id (nullable, for direct FK link)
  - commercial_activity_sessions.contact_id (nullable, for direct FK link)
  - commercial_activity_sessions.deal_id (nullable, for direct FK link to commercial_opportunities)

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-17
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "c3d4e5f6a7b8"
down_revision: Union[str, None] = "b2c3d4e5f6a7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # P1-5: Add direct FK links from activity sessions to company/contact/deal
    op.add_column(
        "commercial_activity_sessions",
        sa.Column("company_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "commercial_activity_sessions",
        sa.Column("contact_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "commercial_activity_sessions",
        sa.Column("deal_id", sa.String(36), nullable=True),
    )

    op.create_index(
        "ix_activity_sessions_company", "commercial_activity_sessions", ["company_id"]
    )
    op.create_index(
        "ix_activity_sessions_contact", "commercial_activity_sessions", ["contact_id"]
    )
    op.create_index(
        "ix_activity_sessions_deal", "commercial_activity_sessions", ["deal_id"]
    )
    op.create_index(
        "ix_activity_sessions_tenant_deal",
        "commercial_activity_sessions",
        ["tenant_id", "deal_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_activity_sessions_tenant_deal", table_name="commercial_activity_sessions"
    )
    op.drop_index(
        "ix_activity_sessions_deal", table_name="commercial_activity_sessions"
    )
    op.drop_index(
        "ix_activity_sessions_contact", table_name="commercial_activity_sessions"
    )
    op.drop_index(
        "ix_activity_sessions_company", table_name="commercial_activity_sessions"
    )
    op.drop_column("commercial_activity_sessions", "deal_id")
    op.drop_column("commercial_activity_sessions", "contact_id")
    op.drop_column("commercial_activity_sessions", "company_id")
