"""Force row-level security on account_funnel and score_observations.

Revision ID: 70193187420d
Revises: u1v2w3x4y5z6

Mechanical audit finding (project-audit/57): both tables already carry
ENABLE ROW LEVEL SECURITY plus a tenant_isolation_* policy from their
originating migrations (n9o0p1q2r3s4_business_effectiveness,
o0p1q2r3s4t5_observation_snapshot), but neither was ever forced. Without
FORCE ROW LEVEL SECURITY the policy does not apply to the table owner or
any future BYPASSRLS-adjacent connection, which is inconsistent with the
canonical DEC-085 pattern used by every other tenant table (verified via
pg_policy + relforcerowsecurity on a fresh ephemeral database: 124 tables
had RLS enabled, only these 2 lacked FORCE). This migration only adds the
missing FORCE clause; it does not touch the existing table shape, policy
definition, or grants.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "70193187420d"
down_revision: str | None = "u1v2w3x4y5z6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = ("account_funnel", "score_observations")


def upgrade() -> None:
    for table in TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" FORCE ROW LEVEL SECURITY'))


def downgrade() -> None:
    for table in TABLES:
        op.execute(sa.text(f'ALTER TABLE "{table}" NO FORCE ROW LEVEL SECURITY'))
