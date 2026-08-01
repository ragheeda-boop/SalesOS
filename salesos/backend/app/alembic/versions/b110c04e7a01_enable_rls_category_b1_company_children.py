"""enable_rls_category_b1_company_children

Revision ID: b110c04e7a01
Revises: b8d4f02a1c06
Create Date: 2026-08-01

DEC-110 / DEC-112 Slice B1 (S04-CATB-01): additive Category B join RLS for
company children `branches` and `licenses` only — raises live
tenant_isolation_* policy count 47 → 49.

Rebased after DEC-113 DB-05 Slice 1: parent is `b8d4f02a1c06` (not
`065d1d3a466b`) so the Alembic graph stays a single head.

Same FORCE / fail-closed / USING+WITH CHECK pattern as Category A
(scripts/generate_rls_policies.generate_join_policy_sql):
  - EXISTS companies WHERE companies.id = child.company_id
    AND companies.tenant_id::text = current_setting('app.tenant_id', true)

Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B2–B7 or DB-05 deferred-8 tables.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    CATEGORY_B1_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "b110c04e7a01"
down_revision: Union[str, None] = "b8d4f02a1c06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B1_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B1_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
