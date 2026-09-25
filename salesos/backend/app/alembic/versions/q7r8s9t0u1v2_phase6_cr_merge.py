"""Merge the Phase 6 and nullable-company-CR migration branches.

Revision ID: q7r8s9t0u1v2
Revises: p6a0b1c2d3e4, p7q8r9s0t1u2
"""

from __future__ import annotations

from collections.abc import Sequence

revision: str = "q7r8s9t0u1v2"
down_revision: str | tuple[str, str] | None = ("p6a0b1c2d3e4", "p7q8r9s0t1u2")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
