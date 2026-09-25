"""Add idempotency keys for client telemetry events.

Revision ID: r1s2t3u4v5w6
Revises: q9r0s1t2u3v4
Create Date: 2026-09-20
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "r1s2t3u4v5w6"
down_revision: Union[str, None] = "q9r0s1t2u3v4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "telemetry_events",
        sa.Column("client_event_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_unique_constraint(
        "uq_telemetry_events_tenant_client_event_id",
        "telemetry_events",
        ["tenant_id", "client_event_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_telemetry_events_tenant_client_event_id",
        "telemetry_events",
        type_="unique",
    )
    op.drop_column("telemetry_events", "client_event_id")
