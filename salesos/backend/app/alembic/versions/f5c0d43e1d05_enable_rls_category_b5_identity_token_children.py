"""enable_rls_category_b5_identity_token_children

Revision ID: f5c0d43e1d05
Revises: e4b9c32d0c04
Create Date: 2026-08-01

DEC-110 / DEC-117 Slice B5 (S04-CATB-05): additive Category B join RLS for
identity token children `password_reset_tokens` and `refresh_token_families`
only — raises live tenant_isolation_* policy count 55 → 57.

Parent paths (DEC-110 inventory; confirmed ORM + 0012 create_table):
  - password_reset_tokens.user_id → users.id (UUID)
  - refresh_token_families.user_id → users.id (UUID)

Parent `users` is Category A with tenant_id. Join predicate is UUID=UUID
(no cast). Same FORCE / fail-closed / USING+WITH CHECK pattern as B1–B4.

Sensitive semantics: policies isolate by parent tenant only — do not add
permissive auth-bypass policies. Unset app.tenant_id remains fail-closed.

Does NOT reopen STORY-02-01 / ALL_TENANT_TABLES (47 Category A intact).
Does NOT enable B6–B7 or DB-05 deferred-8 tables.
Does NOT touch get_db() / DEC-085 set_config.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import (
    CATEGORY_B5_JOIN_TABLES,
    generate_join_policy_sql,
)

revision: str = "f5c0d43e1d05"
down_revision: Union[str, None] = "e4b9c32d0c04"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for child, parent, fk in CATEGORY_B5_JOIN_TABLES:
        sql = generate_join_policy_sql(child, parent, fk)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for child, _parent, _fk in CATEGORY_B5_JOIN_TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{child}" ON "{child}"'))
        op.execute(sa.text(f'ALTER TABLE "{child}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{child}" DISABLE ROW LEVEL SECURITY'))
