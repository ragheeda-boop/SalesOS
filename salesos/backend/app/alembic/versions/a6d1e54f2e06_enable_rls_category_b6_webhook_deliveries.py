"""enable_rls_category_b6_webhook_deliveries

Revision ID: a6d1e54f2e06
Revises: f5c0d43e1d05
Create Date: 2026-08-01

DEC-110 / DEC-118 Slice B6 (S04-CATB-06): additive Category B join RLS for
`webhook_deliveries` only — raises live tenant_isolation_* policy count 57 → 58.

Parent path (DEC-110 inventory; confirmed ORM + 0039 create_table):
  - webhook_deliveries.subscription_id → webhook_subscriptions.id (String(36))

Parent `webhook_subscriptions` is Category A with tenant_id. Join predicate is
varchar=varchar (no cast). Same FORCE / fail-closed / USING+WITH CHECK as B1–B5.

Does NOT ENABLE RLS on deferred-8 `webhook_endpoints` (DB-05 / R-09).
Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B7.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from app.alembic.lib.rls import (
    CATEGORY_B6_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "a6d1e54f2e06"
down_revision: Union[str, None] = "f5c0d43e1d05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B6_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B6_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
