"""Phase 4: EventRuntime DLQ persistence to Postgres.

Revision ID: g1h2i3j4k5l6
Revises: f6a7b8c9d0e1
Create Date: 2026-08-19
"""
from alembic import op
import sqlalchemy as sa

revision = "g1h2i3j4k5l6"
down_revision = "f6a7b8c9d0e1"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_dead_letters",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_id", sa.String(36), nullable=False, index=True),
        sa.Column("event_type", sa.String(128), nullable=False, index=True),
        sa.Column("subscriber_name", sa.String(256), nullable=False),
        sa.Column("error", sa.Text(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_data", sa.JSON(), nullable=True),
        sa.Column("failed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("replayed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_event_dl_tenant_status",
        "event_dead_letters",
        ["tenant_id", "event_type"],
    )
    op.execute("ALTER TABLE event_dead_letters ENABLE ROW LEVEL SECURITY")
    op.execute(
        "CREATE POLICY event_dl_tenant_isolation ON event_dead_letters "
        "USING (tenant_id = current_setting('app.current_tenant_id', true))"
    )
    op.execute("ALTER TABLE event_dead_letters FORCE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS event_dl_tenant_isolation ON event_dead_letters")
    op.execute("ALTER TABLE event_dead_letters DISABLE ROW LEVEL SECURITY")
    op.drop_table("event_dead_letters")
