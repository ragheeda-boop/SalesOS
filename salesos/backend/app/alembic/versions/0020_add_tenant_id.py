"""add tenant_id to tables created by legacy SQL migrations

Adds `tenant_id UUID REFERENCES tenants(id) NOT NULL` and composite
indexes on (tenant_id, company_id) to tables created via raw SQL
(migrations/001_initial.sql) that are missing multi-tenant support.

Tables affected:
  - signals
  - timeline_events
  - government_records
  - documents
  - meetings

Revision ID: 0020
Revises: 0019
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0020"
down_revision: Union[str, None] = "0019"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

TABLES = [
    "signals",
    "timeline_events",
    "government_records",
    "documents",
    "meetings",
]


def upgrade() -> None:
    for table in TABLES:
        op.add_column(
            table,
            sa.Column(
                "tenant_id",
                postgresql.UUID(as_uuid=True),
                sa.ForeignKey("tenants.id", ondelete="CASCADE"),
                nullable=True,
            ),
        )
        op.create_index(
            f"ix_{table}_tenant_company",
            table,
            ["tenant_id", "company_id"],
        )


def downgrade() -> None:
    for table in TABLES:
        op.drop_index(f"ix_{table}_tenant_company", table_name=table)
        op.drop_constraint(
            f"{table}_tenant_id_fkey", table, type_="foreignkey"
        )
        op.drop_column(table, "tenant_id")
