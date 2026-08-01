"""DB-05 Slice 4: ENABLE RLS on deferred-8 tenant tables.

Revision ID: d1a8c35e7f09
Revises: c9f4a21b6e08
Create Date: 2026-08-01

Phase 0 Exit Criterion 7.5 / DEC-123 / DB-05 Slice 4:
  ENABLE + FORCE ROW LEVEL SECURITY + tenant_isolation_* policies on the
  eight DEC-110 deferred tables created in DEC-113 (no RLS until now).

Policy template = scripts.generate_rls_policies.generate_policy_sql
  (same as Category A / DEC-044): fail-closed current_setting, USING+WITH
  CHECK, ::text cast. Nullable tenant_id rows (admin_ai_costs, admin_jobs)
  stay invisible under tenant GUC — no OR IS NULL bypass.

Does NOT fold tables into ALL_TENANT_TABLES (47 Category A count intact).
Does NOT touch get_db() / DEC-085 set_config.
Does NOT DROP companies dead columns (7.4 STOP).
Does NOT run on Railway / production (local/compose only this land).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    DB05_DEFERRED_8_TENANT_TABLES,
    generate_policy_sql,
)

revision: str = "d1a8c35e7f09"
down_revision: Union[str, None] = "c9f4a21b6e08"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table in DB05_DEFERRED_8_TENANT_TABLES:
        sql = generate_policy_sql(table)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for table in DB05_DEFERRED_8_TENANT_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
