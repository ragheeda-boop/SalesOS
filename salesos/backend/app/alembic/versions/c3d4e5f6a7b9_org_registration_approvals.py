"""Queue platform-owner approval before a manager can register an organization.

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8

A public self-registration used to create a tenant immediately. Organization
and manager registration now waits in this table until a designated platform
owner approves it. The row exists before any tenant, so it has no tenant_id
and is not tenant-RLS scoped. Reads and decisions are platform-owner routes;
the unauthenticated insert is the request itself.
"""

from __future__ import annotations

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c3d4e5f6a7b9"
down_revision: str | None = "b2c3d4e5f6a8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "org_registration_approvals",
        sa.Column("id", sa.Uuid(), primary_key=True, nullable=False),
        sa.Column("organization_name", sa.String(length=255), nullable=False),
        sa.Column("manager_email", sa.String(length=255), nullable=False),
        sa.Column("manager_full_name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("decided_by", sa.Uuid(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rejection_reason", sa.String(length=500), nullable=True),
        sa.Column(
            "consumed_tenant_id",
            sa.Uuid(),
            sa.ForeignKey("tenants.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('pending', 'approved', 'rejected', 'consumed')",
            name="ck_org_registration_approvals_status",
        ),
    )
    op.create_index(
        "uq_org_reg_open_email",
        "org_registration_approvals",
        ["manager_email"],
        unique=True,
        postgresql_where=sa.text("status IN ('pending', 'approved')"),
    )
    op.create_index(
        "ix_org_reg_status_created",
        "org_registration_approvals",
        ["status", "created_at"],
    )
    op.execute(
        """
        DO $$
        BEGIN
          IF EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'salesos_app') THEN
            GRANT SELECT, INSERT, UPDATE ON org_registration_approvals TO salesos_app;
          END IF;
        END $$;
        """
    )


def downgrade() -> None:
    op.drop_index("ix_org_reg_status_created", table_name="org_registration_approvals")
    op.drop_index("uq_org_reg_open_email", table_name="org_registration_approvals")
    op.drop_table("org_registration_approvals")
