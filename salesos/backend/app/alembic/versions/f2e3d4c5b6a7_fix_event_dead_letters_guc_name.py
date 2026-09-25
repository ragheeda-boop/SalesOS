"""Fix event_dead_letters RLS policy: wrong GUC variable name.

Revision ID: f2e3d4c5b6a7
Revises: e1d1c1225d00

Mechanical finding (project-audit/75): migration g1h2i3j4k5l6 created
`event_dead_letters`' RLS policy checking `current_setting('app.current_tenant_id', true)`
— a GUC variable name that does not match this codebase's single, universal
convention (`app.tenant_id`, set via `app.database.apply_tenant_guc()` /
`set_config('app.tenant_id', ...)`, used by every other tenant table). No
code anywhere in this repository has ever set `app.current_tenant_id`, so
this policy has been permanently unsatisfiable by any application code
since the table was created — every real INSERT/SELECT under the
restricted runtime role has always failed closed (RLS blocking, not merely
undertested).

This migration drops the wrong policy and replaces it with the canonical
`tenant_isolation_event_dead_letters` policy via
`app.alembic.lib.rls.generate_policy_sql` (same helper as every other
Category A tenant-isolation policy in this repo), which checks the correct
`app.tenant_id` GUC with both `USING` and `WITH CHECK`. Does not change the
table's columns, indexes, or ENABLE/FORCE RLS state (both already correct).
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

from app.alembic.lib.rls import generate_policy_sql

revision: str = "f2e3d4c5b6a7"
down_revision: str | None = "e1d1c1225d00"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_OLD_POLICY = "event_dl_tenant_isolation"
_TABLE = "event_dead_letters"


def upgrade() -> None:
    op.execute(sa.text(f'DROP POLICY IF EXISTS "{_OLD_POLICY}" ON "{_TABLE}"'))
    sql = generate_policy_sql(_TABLE)
    for statement in sql.strip().split(";\n"):
        stmt = statement.strip()
        if stmt:
            op.execute(sa.text(stmt))


def downgrade() -> None:
    op.execute(sa.text(f'DROP POLICY IF EXISTS "tenant_isolation_{_TABLE}" ON "{_TABLE}"'))
    op.execute(
        sa.text(
            f'CREATE POLICY "{_OLD_POLICY}" ON "{_TABLE}" '
            "USING (tenant_id = current_setting('app.current_tenant_id', true))"
        )
    )
