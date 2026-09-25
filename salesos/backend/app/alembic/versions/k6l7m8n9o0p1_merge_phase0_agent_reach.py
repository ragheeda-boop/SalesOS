"""Merge phase0_master_data_foundation and agent_reach_persistence branches.

Both branches are independent — no conflicting table/column definitions.

Revision ID: k6l7m8n9o0p1
Revises: (j4k5l6m7n8o9, j5k6l7m8n9o0)
Create Date: 2026-09-04
"""
from __future__ import annotations

from collections.abc import Sequence

revision: str = "k6l7m8n9o0p1"
down_revision: tuple[str, str] = ("j4k5l6m7n8o9", "j5k6l7m8n9o0")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
