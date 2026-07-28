"""Add unique constraints for synced email/calendar provider IDs.

Revision ID: 0049
Revises: 0048
Create Date: 2026-07-28
"""
from typing import Sequence, Union

from alembic import op

revision: str = "0049"
down_revision: Union[str, None] = "0048"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Deduplicate before unique indexes (keep newest row by updated_at/id).
    op.execute(
        """
        DELETE FROM employee_email_events a
        USING employee_email_events b
        WHERE a.tenant_id = b.tenant_id
          AND a.provider = b.provider
          AND a.provider_message_id = b.provider_message_id
          AND a.id < b.id
        """
    )
    op.execute(
        """
        DELETE FROM employee_calendar_events a
        USING employee_calendar_events b
        WHERE a.tenant_id = b.tenant_id
          AND a.provider = b.provider
          AND a.provider_event_id = b.provider_event_id
          AND a.id < b.id
        """
    )

    op.create_index(
        "uq_email_events_tenant_provider_msg",
        "employee_email_events",
        ["tenant_id", "provider", "provider_message_id"],
        unique=True,
    )
    op.create_index(
        "uq_cal_events_tenant_provider_event",
        "employee_calendar_events",
        ["tenant_id", "provider", "provider_event_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_cal_events_tenant_provider_event", table_name="employee_calendar_events")
    op.drop_index("uq_email_events_tenant_provider_msg", table_name="employee_email_events")
