"""DEC-157: RLS on the 14 live orphan-keep tables.

Revision ID: e1d1c1225d00
Revises: 70193187420d

DEC-157 (Accepted 2026-09-23; project-audit/59, /68) step 4: the final step
of a 4-step remediation for 14 tables governed by DEC-130f's "no DROP
without a dedicated DEC" orphan-keep register that had zero database-level
tenant isolation (isolation relied entirely on hand-written ``WHERE
tenant_id = :tid`` clauses scattered across five runtime modules). Steps 1-3
(semantics ruling, GUC pinning at the five call sites, regression proof with
GUC pinning but RLS still off) landed first; this migration is the RLS DDL
only, using the same canonical DEC-085 policy shape as every other Category A
table (``app.alembic.lib.rls.generate_policy_sql``).

``domain_events`` and ``activity_records`` both have a nullable ``tenant_id``
column. Per the accepted precedent in migration d1a8c35e7f09
(admin_ai_costs/admin_jobs) and the explicit rejection of an
``OR tenant_id IS NULL`` bypass in b7e2f65a3f07, no carve-out is added here:
NULL-tenant rows become invisible under any tenant GUC, fail-closed, same as
every other Category A table. This is a deliberate, ruled-on choice (DEC-157
§3), not an oversight.

Does not touch DEC-130f's KEEP-register posture (RLS is not a schema-shape
change; ``app/db05_orphan_keep.py``'s ``ORPHAN_KEEP_TABLES`` stubs and
``alembic check``'s ``remove_table`` count are unaffected). Does not fold any
of these tables into ``ALL_TENANT_TABLES`` (Category A migrated-only list).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import DEC_157_ORPHAN_KEEP_TENANT_TABLES, generate_policy_sql

revision: str = "e1d1c1225d00"
down_revision: str | None = "70193187420d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table in DEC_157_ORPHAN_KEEP_TENANT_TABLES:
        sql = generate_policy_sql(table)
        for statement in sql.strip().split(";\n"):
            stmt = statement.strip()
            if stmt:
                op.execute(sa.text(stmt))


def downgrade() -> None:
    for table in DEC_157_ORPHAN_KEEP_TENANT_TABLES:
        op.execute(
            sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{table}" ON "{table}"')
        )
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
        op.execute(sa.text(f'ALTER TABLE "{table}" DISABLE ROW LEVEL SECURITY'))
