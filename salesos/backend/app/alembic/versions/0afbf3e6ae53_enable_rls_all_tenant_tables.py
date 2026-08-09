"""enable_rls_all_tenant_tables

Revision ID: 0afbf3e6ae53
Revises: 77214759646c
Create Date: 2026-07-31 14:49:15.592520

Sprint 03 Story 4: enable RLS on all 46 tenant-scoped tables (with migrations).
Uses the same policy template as scripts/generate_rls_policies.py:
  - FORCE ROW LEVEL SECURITY (owner is superuser/BYPASSRLS)
  - current_setting('app.tenant_id', true) — fail-closed (NULL = deny)
  - USING + WITH CHECK — covers both read and write surfaces
  - ::text cast on both sides (uuid vs varchar tenant_id columns)
  - DROP POLICY IF EXISTS — idempotent re-run safe

Prerequisite: app.tenant_id session layer must be live (Story 1).
Without it, RLS returns zero rows on every table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.alembic.lib.rls import ALL_TENANT_TABLES, generate_policy_sql

revision: str = '0afbf3e6ae53'
down_revision: Union[str, None] = '77214759646c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in ALL_TENANT_TABLES:
        sql = generate_policy_sql(table)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt + ""))


def downgrade() -> None:
    for table in ALL_TENANT_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
