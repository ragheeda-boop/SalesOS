"""consolidate contacts: merge contacts_standalone into unified contacts table

The contacts_standalone table (created in 0008) holds CRM-style contacts
that may or may not link to a company. The contacts table (from 0001)
holds company-scoped contacts. This migration:
  1. Adds tenant_id, tags, metadata columns to the unified contacts table
  2. Merges all contacts_standalone rows into contacts
  3. Drops the contacts_standalone table

Revision ID: 0022
Revises: 0021
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0022"
down_revision: Union[str, None] = "0021"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add columns to unified contacts table that exist in contacts_standalone
    op.add_column(
        "contacts",
        sa.Column(
            "tenant_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("tenants.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )
    op.add_column(
        "contacts",
        sa.Column("tags", postgresql.JSONB, nullable=True, server_default="[]"),
    )
    op.add_column(
        "contacts",
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
    )

    # 2. Migrate data from contacts_standalone → contacts
    #    Map columns: contacts_standalone → contacts
    op.execute("""
        INSERT INTO contacts (
            id, tenant_id, company_id,
            name, name_ar, email, phone, mobile,
            position, position_ar, department,
            is_primary, source, confidence_score,
            tags, metadata,
            created_at, updated_at
        )
        SELECT
            id, tenant_id, company_id,
            name, name_ar, email, phone, mobile,
            position, position_ar, department,
            is_primary, source, confidence_score,
            tags, metadata,
            created_at, updated_at
        FROM contacts_standalone
        ON CONFLICT (id) DO NOTHING
    """)

    # 3. Drop contacts_standalone table
    op.drop_table("contacts_standalone")

    # 4. Make tenant_id NOT NULL now that data is merged
    op.execute("ALTER TABLE contacts ALTER COLUMN tenant_id SET NOT NULL")

    # 5. Create indexes for the unified table
    op.create_index(
        "ix_contacts_tenant_email",
        "contacts",
        ["tenant_id", "email"],
    )
    op.create_index(
        "ix_contacts_tenant_company",
        "contacts",
        ["tenant_id", "company_id"],
    )


def downgrade() -> None:
    # Re-create contacts_standalone table
    op.create_table(
        "contacts_standalone",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("company_id", postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column("name", sa.String(500), nullable=False, index=True),
        sa.Column("name_ar", sa.String(500), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("mobile", sa.String(50), nullable=True),
        sa.Column("position", sa.String(255), nullable=True),
        sa.Column("position_ar", sa.String(255), nullable=True),
        sa.Column("department", sa.String(255), nullable=True),
        sa.Column("is_primary", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("source", sa.String(100), nullable=True),
        sa.Column("confidence_score", sa.Float, nullable=True, server_default="0"),
        sa.Column("tags", postgresql.JSONB, nullable=True, server_default="[]"),
        sa.Column("metadata", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # Move standalone contacts back
    op.execute("""
        INSERT INTO contacts_standalone (
            id, tenant_id, company_id,
            name, name_ar, email, phone, mobile,
            position, position_ar, department,
            is_primary, source, confidence_score,
            tags, metadata,
            created_at, updated_at
        )
        SELECT
            id, tenant_id, company_id,
            name, name_ar, email, phone, mobile,
            position, position_ar, department,
            is_primary, source, confidence_score,
            tags, metadata,
            created_at, updated_at
        FROM contacts
        WHERE company_id IS NULL
    """)

    # Remove contacts that were standalone (no company link) from unified table
    op.execute("DELETE FROM contacts WHERE company_id IS NULL")

    # Drop added columns from contacts
    op.drop_index("ix_contacts_tenant_company", table_name="contacts")
    op.drop_index("ix_contacts_tenant_email", table_name="contacts")
    op.drop_column("contacts", "metadata")
    op.drop_column("contacts", "tags")
    op.drop_column("contacts", "tenant_id")
