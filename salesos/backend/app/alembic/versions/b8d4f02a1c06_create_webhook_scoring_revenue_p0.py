"""DB-05 Slice 1: CREATE TABLE for webhook/scoring/revenue P0 R-09 tables.

Revision ID: b8d4f02a1c06
Revises: a7c3e91f0b05
Create Date: 2026-08-01

DEC-113 / DB-05 Slice 1 (domain clusters): additive CREATE only for
  - webhook_endpoints
  - scoring_scorecards
  - revenue_analytics_snapshots

Matches ORM:
  - domains/workflow/db_models.py
  - domains/scoring/infrastructure/postgres_repository.py
  - domains/revenue/analytics/postgres_repo.py

Does NOT ENABLE RLS. Does NOT touch get_db() / DEC-085 set_config.
Idempotent: skip create when table already exists (init_db / create_all drift).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "b8d4f02a1c06"
down_revision: Union[str, None] = "a7c3e91f0b05"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "webhook_endpoints"):
        op.create_table(
            "webhook_endpoints",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False),
            sa.Column("url", sa.String(1024), nullable=False),
            sa.Column("name", sa.String(255), nullable=False, server_default=""),
            sa.Column("auth_type", sa.String(20), nullable=False, server_default="none"),
            sa.Column(
                "auth_config",
                postgresql.JSONB(),
                nullable=False,
                server_default=sa.text("'{}'::jsonb"),
            ),
            sa.Column("secret", sa.String(512), nullable=False, server_default=""),
            sa.Column("status", sa.String(20), nullable=False, server_default="active"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_webhook_endpoints_tenant_id", "webhook_endpoints", ["tenant_id"])
        op.create_index("ix_webhook_endpoints_status", "webhook_endpoints", ["status"])

    if not _table_exists(conn, "scoring_scorecards"):
        op.create_table(
            "scoring_scorecards",
            sa.Column("id", sa.String(), primary_key=True),
            sa.Column("tenant_id", sa.String(), nullable=False),
            sa.Column("target_id", sa.String(), nullable=False),
            sa.Column("target_type", sa.String(), nullable=False, server_default="company"),
            sa.Column("overall_score", sa.Float(), nullable=False, server_default="0"),
            sa.Column("overall_confidence", sa.String(), nullable=False, server_default="low"),
            sa.Column(
                "scores_json",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'{}'::json"),
            ),
            sa.Column("generated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        )
        op.create_index("ix_scoring_scorecards_tenant_id", "scoring_scorecards", ["tenant_id"])
        op.create_index("ix_scoring_scorecards_target_id", "scoring_scorecards", ["target_id"])
        op.create_index(
            "ix_scorecards_tenant_target",
            "scoring_scorecards",
            ["tenant_id", "target_id", "generated_at"],
        )

    if not _table_exists(conn, "revenue_analytics_snapshots"):
        op.create_table(
            "revenue_analytics_snapshots",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(64), nullable=False),
            sa.Column("period_start", sa.DateTime(timezone=True), nullable=True),
            sa.Column("period_end", sa.DateTime(timezone=True), nullable=True),
            sa.Column(
                "values",
                sa.JSON(),
                nullable=False,
                server_default=sa.text("'[]'::json"),
            ),
            sa.Column(
                "generated_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        )
        op.create_index(
            "ix_revenue_analytics_snapshots_tenant_id",
            "revenue_analytics_snapshots",
            ["tenant_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    if _table_exists(conn, "revenue_analytics_snapshots"):
        op.drop_index(
            "ix_revenue_analytics_snapshots_tenant_id",
            table_name="revenue_analytics_snapshots",
        )
        op.drop_table("revenue_analytics_snapshots")
    if _table_exists(conn, "scoring_scorecards"):
        op.drop_index("ix_scorecards_tenant_target", table_name="scoring_scorecards")
        op.drop_index("ix_scoring_scorecards_target_id", table_name="scoring_scorecards")
        op.drop_index("ix_scoring_scorecards_tenant_id", table_name="scoring_scorecards")
        op.drop_table("scoring_scorecards")
    if _table_exists(conn, "webhook_endpoints"):
        op.drop_index("ix_webhook_endpoints_status", table_name="webhook_endpoints")
        op.drop_index("ix_webhook_endpoints_tenant_id", table_name="webhook_endpoints")
        op.drop_table("webhook_endpoints")
