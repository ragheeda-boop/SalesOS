"""enable_rls_category_b3_analytics_children

Revision ID: d3f8a21c9b03
Revises: c221d15f8b02
Create Date: 2026-08-01

DEC-110 / DEC-115 Slice B3 (S04-CATB-03): additive Category B join RLS for
analytics children `analytics_report_executions` and `analytics_report_shares`
only — raises live tenant_isolation_* policy count 51 → 53.

Parent paths (DEC-110 inventory; confirmed ORM + 0014 / 77214759646c create_table):
  - analytics_report_executions.report_id → analytics_reports.id
  - analytics_report_shares.report_id → analytics_reports.id

Same FORCE / fail-closed / USING+WITH CHECK pattern as Category A / B1 / B2
(scripts/generate_rls_policies.generate_join_policy_sql).

Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B4–B7 or DB-05 deferred-8 tables.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.alembic.lib.rls import (
    CATEGORY_B3_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "d3f8a21c9b03"
down_revision: Union[str, None] = "c221d15f8b02"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B3_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B3_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
