"""Add missing columns to companies table

Several columns exist in the ORM model but were never added to the DB:
fax, website, currency, industry, isic_code, isic_description,
incorporation_date, expiry_date, is_golden_record, source_ids, tags, metadata

Revision ID: 0034
Revises: 0033
Create Date: 2026-07-15
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql.schema import Column

revision: str = "0034"
down_revision: Union[str, None] = "0033"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _col_exists(conn, table: str, column: str) -> bool:
    inspector = sa.inspect(conn)
    columns = [c["name"] for c in inspector.get_columns(table)]
    return column in columns


def upgrade() -> None:
    conn = op.get_bind()

    additions: list[tuple[str, Column]] = [
        ("fax", sa.Column("fax", sa.String(50), nullable=True)),
        ("website", sa.Column("website", sa.String(500), nullable=True)),
        ("currency", sa.Column("currency", sa.String(10), nullable=True, server_default="SAR")),
        ("industry", sa.Column("industry", sa.String(200), nullable=True)),
        ("isic_code", sa.Column("isic_code", sa.String(20), nullable=True)),
        ("isic_description", sa.Column("isic_description", sa.String(500), nullable=True)),
        ("incorporation_date", sa.Column("incorporation_date", sa.Date, nullable=True)),
        ("expiry_date", sa.Column("expiry_date", sa.Date, nullable=True)),
        ("is_golden_record", sa.Column("is_golden_record", sa.Boolean, nullable=True, server_default="false")),
        ("source_ids", sa.Column("source_ids", JSONB, nullable=True, server_default="[]")),
        ("tags", sa.Column("tags", JSONB, nullable=True, server_default="[]")),
        ("metadata", sa.Column("metadata", JSONB, nullable=True, server_default="{}")),
    ]

    for col_name, col in additions:
        if not _col_exists(conn, "companies", col_name):
            op.add_column("companies", col)


def downgrade() -> None:
    for col_name in ["metadata", "tags", "source_ids", "is_golden_record",
                      "expiry_date", "incorporation_date", "isic_description",
                      "isic_code", "industry", "currency", "website", "fax"]:
        try:
            op.drop_column("companies", col_name)
        except Exception:
            pass
