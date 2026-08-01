"""enable_rls_category_b4_decision_center_children

Revision ID: e4b9c32d0c04
Revises: d3f8a21c9b03
Create Date: 2026-08-01

DEC-110 / DEC-116 Slice B4 (S04-CATB-04): additive Category B join RLS for
decision-center children `decision_center_audits` and `decision_center_feedback`
only — raises live tenant_isolation_* policy count 53 → 55.

Parent paths (DEC-110 inventory; confirmed ORM + 0038 create_table):
  - decision_center_audits.decision_id → decision_center_decisions.id
  - decision_center_feedback.decision_id → decision_center_decisions.id

Parent PK is UUID (BaseModel); child FK is String(64). Join predicate uses
p.id::text via generate_join_policy_sql(..., cast_parent_pk_to_text=True)
— same cast pattern as domains/decision_center/postgres_repo.py feedback join.

Same FORCE / fail-closed / USING+WITH CHECK pattern as Category A / B1–B3.

Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B5–B7 or DB-05 deferred-8 tables.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    CATEGORY_B4_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "e4b9c32d0c04"
down_revision: Union[str, None] = "d3f8a21c9b03"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B4_JOIN_TABLES:
        sql = generate_join_policy_sql(
            child, parent, fk, cast_parent_pk_to_text=True
        )
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B4_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
