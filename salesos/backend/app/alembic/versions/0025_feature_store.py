"""feature_store: create feature_definitions and feature_values tables

Generic feature store tables that feed the ScoringEngine and Decision Platform.
Unlike company_features (runtime-level, company-only), these tables are entity-
agnostic and support arbitrary feature definitions with TTL-based expiry.

Revision ID: 0025
Revises: 0024
Create Date: 2026-07-12
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import func

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "feature_definitions",
        sa.Column("key", sa.String(255), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("feature_type", sa.String(50), server_default="numeric"),
        sa.Column("domain", sa.String(100), server_default="general"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=func.now(),
        ),
    )

    op.create_table(
        "feature_values",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "feature_key",
            sa.String(255),
            sa.ForeignKey("feature_definitions.key", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("entity_id", sa.String(36), nullable=False),
        sa.Column("entity_type", sa.String(50), nullable=False),
        sa.Column("value", sa.JSON, nullable=True),
        sa.Column(
            "computed_at",
            sa.DateTime(timezone=True),
            server_default=func.now(),
        ),
        sa.Column("ttl_seconds", sa.Integer, server_default="3600"),
    )

    op.create_index(
        "idx_feature_values_lookup",
        "feature_values",
        ["entity_type", "entity_id", "feature_key"],
    )


def downgrade() -> None:
    op.drop_index("idx_feature_values_lookup", table_name="feature_values")
    op.drop_table("feature_values")
    op.drop_table("feature_definitions")
