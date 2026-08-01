"""enable_rls_category_b2_commercial_children

Revision ID: c221d15f8b02
Revises: b110c04e7a01
Create Date: 2026-08-01

DEC-110 / DEC-114 Slice B2 (S04-CATB-02): additive Category B join RLS for
commercial children `commercial_activities` and `commercial_quote_lines`
only — raises live tenant_isolation_* policy count 49 → 51.

Parent paths (DEC-110 inventory; confirmed ORM + 0007 create_table):
  - commercial_activities.session_id → commercial_activity_sessions.id
  - commercial_quote_lines.quote_id → commercial_quotes.id

Same FORCE / fail-closed / USING+WITH CHECK pattern as Category A / B1
(scripts/generate_rls_policies.generate_join_policy_sql).

Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B3–B7 or DB-05 deferred-8 tables.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    CATEGORY_B2_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "c221d15f8b02"
down_revision: Union[str, None] = "b110c04e7a01"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B2_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B2_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
