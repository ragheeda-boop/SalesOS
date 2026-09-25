"""Link seller outcomes to a verified commercial opportunity.

Revision ID: a0b1c2d3e4f5
Revises: z9a0b1c2d3e4
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "a0b1c2d3e4f5"
down_revision: str | None = "z9a0b1c2d3e4"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Nullable fields preserve every historical outcome. The API verifies a
    # non-null opportunity against the caller's tenant before insertion.
    op.add_column("action_outcomes", sa.Column("opportunity_id", sa.String(36), nullable=True))
    op.add_column("action_outcomes", sa.Column("idempotency_key", sa.String(128), nullable=True))
    op.create_index(
        "ix_action_outcomes_tenant_opportunity_occurred",
        "action_outcomes",
        ["tenant_id", "opportunity_id", "occurred_at"],
    )
    op.create_unique_constraint(
        "uq_action_outcomes_tenant_action_idempotency",
        "action_outcomes",
        ["tenant_id", "action_id", "idempotency_key"],
    )
    # The original HITL migration created the policies but did not grant the
    # restricted runtime role the privileges required to use the lifecycle.
    # Keep the owner role out of request handling; RLS still decides scope.
    op.execute(
        sa.text(
            "DO $grant$ BEGIN IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN "
            "GRANT SELECT, INSERT ON nba_feedback, action_outcomes TO salesos_app; "
            "GRANT SELECT, INSERT, UPDATE ON sales_followups TO salesos_app; "
            "END IF; END $grant$;"
        )
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_action_outcomes_tenant_action_idempotency",
        "action_outcomes",
        type_="unique",
    )
    op.drop_index("ix_action_outcomes_tenant_opportunity_occurred", table_name="action_outcomes")
    op.drop_column("action_outcomes", "idempotency_key")
    op.drop_column("action_outcomes", "opportunity_id")
