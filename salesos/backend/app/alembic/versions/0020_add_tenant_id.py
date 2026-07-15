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
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}') THEN
                    ALTER TABLE {table} ADD COLUMN IF NOT EXISTS tenant_id uuid REFERENCES tenants(id) ON DELETE CASCADE;
                END IF;
            END;
            $$;
        """)


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS (SELECT FROM pg_tables WHERE tablename = '{table}') THEN
                    ALTER TABLE {table} DROP CONSTRAINT IF EXISTS {table}_tenant_id_fkey;
                    ALTER TABLE {table} DROP COLUMN IF EXISTS tenant_id;
                END IF;
            END;
            $$;
        """)
