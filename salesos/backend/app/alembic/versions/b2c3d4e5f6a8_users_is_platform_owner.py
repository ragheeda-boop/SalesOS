"""Add users.is_platform_owner: explicit Owner Platform marker.

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7

Owner Platform access (/owner/login and every require_owner_role_dep route)
previously required only tenant role "admin". Self-registered tenant creators
now become admin of their own tenant, so tenant admin must no longer imply
platform owner. Default false and no backfill: existing admins (including
earlier self-registrants) cannot be told apart from real owners, so each
platform owner is designated explicitly by an ops UPDATE.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a8"
down_revision: str | None = "a1b2c3d4e5f7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_platform_owner",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_column("users", "is_platform_owner")
