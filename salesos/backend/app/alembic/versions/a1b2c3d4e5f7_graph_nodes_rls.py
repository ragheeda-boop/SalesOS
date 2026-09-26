"""Enable RLS on graph_nodes: a real tenant_id column, never registered.

Revision ID: a1b2c3d4e5f7
Revises: f2e3d4c5b6a7

Mechanical audit finding (project-audit/132): a direct pg_class/
information_schema census of tenant_id-bearing tables with RLS disabled
found `graph_nodes` (created in 0004_knowledge_graph.py, kept live under
DEC-130f's "no DROP without a dedicated DEC" register) with a real,
NOT NULL, varchar(36) `tenant_id` column and zero RLS — never added to
`ALL_TENANT_TABLES` at creation time. Confirmed via exhaustive grep that no
application code anywhere references this table by name today (every
`graph_nodes` hit in the codebase is the unrelated `merge_graph_nodes()`
method name on the knowledge-graph runtime, which never touches this
table) -- unlike DEC-157's 14 tables, there is no live caller to pin a
tenant GUC for first; this is a pure registry-gap closure; adding it to
`ALL_TENANT_TABLES` for consistency with every other Category A table.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql

revision: str = "a1b2c3d4e5f7"
down_revision: str | None = "f2e3d4c5b6a7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("graph_nodes",)


def upgrade() -> None:
    for table in TABLES:
        sql = generate_policy_sql(table)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for table in TABLES:
        op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"'))
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
