"""Merge ADR-030 (a1b9c8d7e6f5) and agent_tasks (f4aee055fd6e) branches.

Both branches originated from f7a1b82c3d09 and are independent —
no conflicting table/column definitions.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "m5b0a1c2d3e4"
down_revision: tuple[str, str] = ("a1b9c8d7e6f5", "f4aee055fd6e")
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
