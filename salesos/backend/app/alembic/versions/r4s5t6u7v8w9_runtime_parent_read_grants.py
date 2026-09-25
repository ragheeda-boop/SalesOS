"""Grant the restricted runtime role the parent reads needed by new workflows.

Revision ID: r4s5t6u7v8w9
Revises: b1c2d3e4f5a6

RLS remains the tenant boundary.  These are table privileges only: a seller
workflow must be able to verify the tenant-owned company/contact/opportunity
that it references, while PostgreSQL still filters all rows through the
existing FORCE RLS policies.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "r4s5t6u7v8w9"
down_revision: str | None = "b1c2d3e4f5a6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        sa.text(
            "DO $grant$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN "
            "GRANT SELECT ON companies, contacts, commercial_opportunities TO salesos_app; "
            "GRANT SELECT, INSERT, UPDATE, DELETE ON opportunity_contacts TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text(
            "DO $revoke$ BEGIN "
            "IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN "
            "REVOKE SELECT ON companies, contacts, commercial_opportunities FROM salesos_app; "
            "REVOKE SELECT, INSERT, UPDATE, DELETE ON opportunity_contacts FROM salesos_app; "
            "END IF; END $revoke$;"
        )
    )
