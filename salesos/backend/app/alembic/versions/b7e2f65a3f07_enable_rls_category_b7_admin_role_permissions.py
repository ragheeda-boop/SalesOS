"""enable_rls_category_b7_admin_role_permissions

Revision ID: b7e2f65a3f07
Revises: a6d1e54f2e06
Create Date: 2026-08-01

DEC-110 / DEC-119 Slice B7 (S04-CATB-07): additive Category B join RLS for
`admin_role_permissions` only — raises live tenant_isolation_* policy count
58 → 59.

Parent path (DEC-110 inventory; confirmed ORM + 0037 create_table):
  - admin_role_permissions.role_id → admin_roles.id (String(100))

Parent `admin_roles` is Category A with **nullable** tenant_id. Join predicate
matches Category A fail-closed equality (p.tenant_id::text = app.tenant_id GUC).
Do NOT add permissive `OR p.tenant_id IS NULL` — that would expose global /
owner-seeded role permission maps to every tenant session.

NULL-tenant parent roles remain invisible under a tenant GUC (same as parent
Category A). Owner / BYPASSRLS paths are out of band for this policy shape.

Same FORCE / fail-closed / USING+WITH CHECK as B1–B6.

Does NOT ENABLE RLS on deferred-8 admin_* billing tables (DB-05 / R-09).
Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    CATEGORY_B7_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "b7e2f65a3f07"
down_revision: Union[str, None] = "a6d1e54f2e06"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B7_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B7_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
