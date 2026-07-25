"""Ensure graph_edges / graph_nodes exist (0004 drift repair)

Revision 0004 defined these tables for KG SQL fallback, but some local DBs
reached head (0039) without the physical relations (stamp / recreate drift).
This migration is idempotent: create only if missing.

Revision ID: 0040
Revises: 0039
Create Date: 2026-07-22
"""
from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0040"
down_revision: str | None = "0039"
branch_labels: str | None = None
depends_on: str | None = None


def _table_exists(conn, table: str) -> bool:
    inspector = sa.inspect(conn)
    return table in inspector.get_table_names()


def _index_exists(conn, table: str, index_name: str) -> bool:
    inspector = sa.inspect(conn)
    return any(idx["name"] == index_name for idx in inspector.get_indexes(table))


def upgrade() -> None:
    conn = op.get_bind()

    if not _table_exists(conn, "graph_edges"):
        op.create_table(
            "graph_edges",
            sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
            sa.Column("source_id", sa.String(64), nullable=False),
            sa.Column("target_id", sa.String(64), nullable=False),
            sa.Column("edge_type", sa.String(50), nullable=False),
            sa.Column("properties", postgresql.JSONB, nullable=True),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )
        op.create_index("ix_graph_edges_source", "graph_edges", ["source_id", "edge_type"])
        op.create_index("ix_graph_edges_target", "graph_edges", ["target_id", "edge_type"])
        op.create_index(
            "ix_graph_edges_unique",
            "graph_edges",
            ["source_id", "target_id", "edge_type"],
            unique=True,
        )
    else:
        if not _index_exists(conn, "graph_edges", "ix_graph_edges_source"):
            op.create_index("ix_graph_edges_source", "graph_edges", ["source_id", "edge_type"])
        if not _index_exists(conn, "graph_edges", "ix_graph_edges_target"):
            op.create_index("ix_graph_edges_target", "graph_edges", ["target_id", "edge_type"])
        if not _index_exists(conn, "graph_edges", "ix_graph_edges_unique"):
            op.create_index(
                "ix_graph_edges_unique",
                "graph_edges",
                ["source_id", "target_id", "edge_type"],
                unique=True,
            )

    if not _table_exists(conn, "graph_nodes"):
        op.create_table(
            "graph_nodes",
            sa.Column("id", sa.String(64), primary_key=True),
            sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
            sa.Column("labels", postgresql.ARRAY(sa.String(50)), nullable=False),
            sa.Column("properties", postgresql.JSONB, nullable=True),
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
        )
        op.execute(
            """
            CREATE INDEX ix_graph_nodes_search ON graph_nodes
            USING GIN (to_tsvector('simple', COALESCE(properties->>'name_ar', '') || ' ' ||
                                             COALESCE(properties->>'name_en', '') || ' ' ||
                                             COALESCE(properties->>'cr_number', '')))
            """
        )


def downgrade() -> None:
    # Do not drop tables that may pre-exist from 0004 on healthy DBs.
    pass
