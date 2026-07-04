"""contact module: create contacts_standalone table

Creates:
  - contacts_standalone — standalone CRM-style contacts (may link to a company)

Revision ID: 0008
Revises: 0007
Create Date: 2026-07-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0008"
down_revision: Union[str, None] = "0007"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "contacts_standalone",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("name_ar", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile", sa.String(50), nullable=True),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("position_ar", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True, server_default="0"),
        sa.Column("tags", postgresql.JSONB, nullable=True, server_default="[]"),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_contacts_standalone_tenant_email", "contacts_standalone", ["tenant_id", "email"])
    op.create_index("ix_contacts_standalone_tenant_company", "contacts_standalone", ["tenant_id", "company_id"])


def downgrade() -> None:
    op.drop_table("contacts_standalone")
