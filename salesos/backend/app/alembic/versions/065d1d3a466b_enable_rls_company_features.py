"""enable_rls_company_features

Revision ID: 065d1d3a466b
Revises: 07e3ec4084fc
Create Date: 2026-08-01

STORY-02-01 Option B (DEC-044): additive Category-A RLS for company_features
only — raises governed policy count 46 → 47. Same template as
scripts/generate_rls_policies.generate_policy_sql / 0afbf3e6ae53:
  - FORCE ROW LEVEL SECURITY
  - current_setting('app.tenant_id', true) — fail-closed
  - USING + WITH CHECK
  - ::text cast on both sides

Does NOT enable RLS on the eight R-09 drift tables (no CREATE TABLE).
Does NOT invent Category B join policies (Sprint 04).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from scripts.generate_rls_policies import generate_policy_sql

revision: str = "065d1d3a466b"
down_revision: Union[str, None] = "07e3ec4084fc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_TABLE = "company_features"


def upgrade() -> None:
    sql = generate_policy_sql(_TABLE)
    for statement in sql.strip().split(";\n"):
        stmt = statement.strip()
        if stmt:
            op.execute(sa.text(stmt))


def downgrade() -> None:
    op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{_TABLE}" ON "{_TABLE}"'))
    op.execute(sa.text(f'ALTER TABLE "{_TABLE}" NO FORCE ROW LEVEL SECURITY'))
    op.execute(sa.text(f'ALTER TABLE "{_TABLE}" DISABLE ROW LEVEL SECURITY'))
