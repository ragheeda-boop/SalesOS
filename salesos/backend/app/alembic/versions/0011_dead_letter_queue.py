"""dead letter queue table for failed pipeline records
Revision ID: 0011
Revises: 0010
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0011"
down_revision: Union[str, None] = "0010"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "dead_letter_queue",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("tenant_id", sa.String(36), nullable=False),
        sa.Column("source_slug", sa.String(100), nullable=False),
        sa.Column("cr_number", sa.String(50), nullable=True),
        sa.Column("stage", sa.String(50), nullable=False),
        sa.Column("record_data", postgresql.JSONB(), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=False),
        sa.Column("error_type", sa.String(100), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("status", sa.String(20), nullable=False, server_default="failed"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_retry_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_dlq_tenant_status", "dead_letter_queue", ["tenant_id", "status"])
    op.create_index("ix_dlq_created_at", "dead_letter_queue", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_dlq_created_at", table_name="dead_letter_queue")
    op.drop_index("ix_dlq_tenant_status", table_name="dead_letter_queue")
    op.drop_table("dead_letter_queue")
