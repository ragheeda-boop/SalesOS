"""knowledge graph: add graph_edges table for SQL fallback

Creates:
  - public.graph_edges (SQL fallback for graph relationships)
  - public.graph_nodes (SQL fallback for graph node cache)

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-30
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "graph_edges",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("source_id", sa.String(64), nullable=False),
        sa.Column("target_id", sa.String(64), nullable=False),
        sa.Column("edge_type", sa.String(50), nullable=False),
        sa.Column("properties", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_graph_edges_source", "graph_edges", ["source_id", "edge_type"])
    op.create_index("ix_graph_edges_target", "graph_edges", ["target_id", "edge_type"])
    op.create_index("ix_graph_edges_unique", "graph_edges",
                    ["source_id", "target_id", "edge_type"], unique=True)

    op.create_table(
        "graph_nodes",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("tenant_id", sa.String(36), nullable=False, index=True),
        sa.Column("labels", postgresql.ARRAY(sa.String(50)), nullable=False),
        sa.Column("properties", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True),
                  server_default=sa.text("now()"), nullable=False),
    )

    # ── Full-text index on node properties for graph search ────
    op.execute("""
        CREATE INDEX ix_graph_nodes_search ON graph_nodes
        USING GIN (to_tsvector('simple', COALESCE(properties->>'name_ar', '') || ' ' ||
                                         COALESCE(properties->>'name_en', '') || ' ' ||
                                         COALESCE(properties->>'cr_number', '')))
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_graph_nodes_search")
    op.drop_table("graph_nodes")
    op.drop_table("graph_edges")
