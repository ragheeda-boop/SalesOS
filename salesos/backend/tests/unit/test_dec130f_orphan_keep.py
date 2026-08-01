"""DEC-130f / criterion 7.6 Slice 5f: orphan KEEP tables must stay registered.

Prevents silent reintroduction of remove_table DROP proposals for live
enrichment / decision / RAG / graph_nodes tables. No DROP without dedicated DEC.
"""

from __future__ import annotations

from app.database import Base
from app.db05_orphan_keep import ORPHAN_KEEP_TABLES


def test_orphan_keep_tables_registered_on_base_metadata():
    missing = sorted(name for name in ORPHAN_KEEP_TABLES if name not in Base.metadata.tables)
    assert missing == [], (
        "DEC-130f / criterion 7.6: orphan KEEP tables missing from Base.metadata "
        f"(must KEEP/register, never DROP): {missing}"
    )


def test_orphan_keep_inventory_size():
    assert len(ORPHAN_KEEP_TABLES) == 15


def test_vectors_core_table_keeps_timestamps():
    """DEC-130f: vectors.created_at / updated_at live — must be on Core Table."""
    cols = set(Base.metadata.tables["vectors"].c.keys())
    assert "created_at" in cols and "updated_at" in cols
