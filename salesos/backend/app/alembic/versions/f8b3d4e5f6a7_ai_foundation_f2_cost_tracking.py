"""AI Foundation F2 — Persistent LLM cost tracking with budget enforcement.

Creates:
  - llm_cost_entries: per-call cost records (tenant-aware, provider/model attribution)
  - tenant_llm_budgets: per-tenant budget configuration with current-period spend

Revision ID: f8b3d4e5f6a7
Revises: c1d2e3f4a5b6
Create Date: 2026-08-10
"""
from __future__ import annotations

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "f8b3d4e5f6a7"
down_revision: Union[str, None] = "c1d2e3f4a5b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "llm_cost_entries",
        sa.Column("id", sa.String(32), primary_key=True),
        sa.Column("tenant_id", sa.String(64), nullable=False, index=True),
        sa.Column("user_id", sa.String(64), nullable=True),
        sa.Column("provider", sa.String(64), nullable=False),
        sa.Column("model", sa.String(128), nullable=False),
        sa.Column("operation", sa.String(32), nullable=False, server_default="completion"),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cost", sa.Numeric(12, 8), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0"),
        sa.Column("success", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("error", sa.String(256), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    op.create_index("ix_llm_cost_entries_tenant_ts", "llm_cost_entries",
                    ["tenant_id", "timestamp"])
    op.create_index("ix_llm_cost_entries_provider", "llm_cost_entries",
                    ["provider"])
    op.create_index("ix_llm_cost_entries_model", "llm_cost_entries",
                    ["model"])

    op.create_table(
        "tenant_llm_budgets",
        sa.Column("tenant_id", sa.String(64), primary_key=True),
        sa.Column("monthly_budget_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("period_start", sa.Date(), nullable=False,
                  server_default=sa.text("date_trunc('month', now())::date")),
        sa.Column("period_spend_cents", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("is_enforced", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("tenant_llm_budgets")
    op.drop_index("ix_llm_cost_entries_model", table_name="llm_cost_entries")
    op.drop_index("ix_llm_cost_entries_provider", table_name="llm_cost_entries")
    op.drop_index("ix_llm_cost_entries_tenant_ts", table_name="llm_cost_entries")
    op.drop_table("llm_cost_entries")
