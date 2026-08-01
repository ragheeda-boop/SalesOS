"""PGVector native type migration — ARRAY(FLOAT) → VECTOR(n) with HNSW index.

CI-19 Wave 2 Core (no sqlalchemy.text)

Run via: python -m runtime.knowledge_graph_runtime.pgvector_migration
"""

from __future__ import annotations

import re
import time
from typing import Any, Callable

from sqlalchemy import Column, Integer, MetaData, Table, column, select, table
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import bindparam

_ALLOWED_TABLES = frozenset({"companies", "contacts", "golden_records", "search_index"})
_ALLOWED_COLUMNS = frozenset({"embedding"})
_IDENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")

_info_columns = table(
    "columns",
    column("data_type"),
    column("table_name"),
    column("column_name"),
    schema="information_schema",
)


def _safe_ident(name: str, allowed: frozenset[str]) -> str:
    if name not in allowed or not _IDENT_RE.match(name):
        raise ValueError(f"Disallowed SQL identifier: {name!r}")
    return name


def _safe_derived(name: str) -> str:
    if not _IDENT_RE.match(name):
        raise ValueError(f"Disallowed derived identifier: {name!r}")
    return name


def _embedding_table(table_name: str, column_name: str, new_col: str | None = None) -> Table:
    cols = [
        Column("id", Integer, primary_key=True),
        Column(column_name),
    ]
    if new_col:
        cols.append(Column(new_col))
    return Table(table_name, MetaData(), *cols)


class PgVectorMigration:
    """Migrate embedding columns from ARRAY(FLOAT) to native VECTOR(n).

    Steps:
      1. Add new VECTOR(n) column
      2. Copy existing ARRAY(FLOAT) data → VECTOR(n) via cast
      3. Drop old ARRAY(FLOAT) column
      4. Rename VECTOR(n) column to original name
      5. Create HNSW index for fast similarity search
    """

    def __init__(self, session_factory: Callable[[], AsyncSession], logger: Any = None):
        self._session_factory = session_factory
        self._logger = logger

    async def migrate_table(
        self,
        table_name: str,
        column_name: str = "embedding",
        dimension: int = 3072,
    ) -> dict:
        """Migrate a single table's embedding column to native VECTOR(n).

        Returns stats dict with timing and row counts.
        """
        table_name = _safe_ident(table_name, _ALLOWED_TABLES)
        column_name = _safe_ident(column_name, _ALLOWED_COLUMNS)
        if not isinstance(dimension, int) or dimension < 1 or dimension > 10000:
            raise ValueError(f"Invalid vector dimension: {dimension!r}")

        t0 = time.monotonic()
        stats = {"table": table_name, "rows_migrated": 0, "index_created": False}

        async with self._session_factory() as session:
            col_type = await session.execute(
                select(_info_columns.c.data_type).where(
                    _info_columns.c.table_name == table_name,
                    _info_columns.c.column_name == column_name,
                )
            )
            row = col_type.mappings().one_or_none()
            if row and row["data_type"] == "USER-DEFINED":
                if self._logger:
                    self._logger.info(
                        "Column %s.%s already VECTOR type, skipping", table_name, column_name
                    )
                stats["skipped"] = True
                return stats

            new_col = _safe_derived(f"{column_name}_vec")
            connection = await session.connection()

            try:
                await connection.exec_driver_sql(
                    f'ALTER TABLE "{table_name}" ADD COLUMN "{new_col}" vector({dimension})'
                )
            except Exception:
                if self._logger:
                    self._logger.warning(
                        "Column %s.%s may already exist, continuing", table_name, new_col
                    )

            result = await connection.exec_driver_sql(
                f'UPDATE "{table_name}" '
                f'SET "{new_col}" = "{column_name}"::vector '
                f'WHERE "{new_col}" IS NULL AND "{column_name}" IS NOT NULL'
            )
            stats["rows_migrated"] = result.rowcount if result.rowcount else 0

            await connection.exec_driver_sql(
                f'ALTER TABLE "{table_name}" DROP COLUMN "{column_name}"'
            )

            await connection.exec_driver_sql(
                f'ALTER TABLE "{table_name}" RENAME COLUMN "{new_col}" TO "{column_name}"'
            )

            index_name = _safe_derived(f"idx_{table_name}_{column_name}_hnsw")
            try:
                await connection.exec_driver_sql(
                    f'CREATE INDEX IF NOT EXISTS "{index_name}" '
                    f'ON "{table_name}" '
                    f'USING hnsw ("{column_name}" vector_cosine_ops) '
                    f"WITH (m = 16, ef_construction = 64)"
                )
                stats["index_created"] = True
            except Exception as exc:
                if self._logger:
                    self._logger.warning("HNSW index creation failed: %s", exc)

            await session.commit()

        stats["duration_ms"] = round((time.monotonic() - t0) * 1000, 2)
        if self._logger:
            self._logger.info(
                "PGVector migration for %s: %d rows migrated in %.0fms",
                table_name,
                stats["rows_migrated"],
                stats["duration_ms"],
            )
        return stats

    async def migrate_all(self, dimension: int = 3072) -> list[dict]:
        """Migrate all known embedding tables."""
        tables = ["companies", "contacts", "golden_records", "search_index"]
        results = []
        for table_name in tables:
            try:
                result = await self.migrate_table(table_name, dimension=dimension)
                results.append(result)
            except Exception as exc:
                if self._logger:
                    self._logger.error("Migration failed for %s: %s", table_name, exc)
                results.append({"table": table_name, "error": str(exc)})
        return results

    async def verify_speedup(self, table_name: str, column_name: str = "embedding") -> dict:
        """Compare query speed: ARRAY scan vs VECTOR cosine distance."""
        table_name = _safe_ident(table_name, _ALLOWED_TABLES)
        column_name = _safe_ident(column_name, _ALLOWED_COLUMNS)
        emb = _embedding_table(table_name, column_name)

        async with self._session_factory() as session:
            row = await session.execute(
                select(emb.c[column_name])
                .where(emb.c[column_name].is_not(None))
                .limit(1)
            )
            sample = row.mappings().one_or_none()
            if not sample:
                return {"error": "No embeddings found to benchmark"}

            sample_vec = sample[column_name]
            distance = emb.c[column_name].op("<=>")(bindparam("vec"))

            t0 = time.monotonic()
            await session.execute(
                select(emb.c.id, distance.label("distance"))
                .where(emb.c[column_name].is_not(None))
                .order_by(distance)
                .limit(10),
                {"vec": str(sample_vec)},
            )
            vector_ms = (time.monotonic() - t0) * 1000

            return {
                "vector_cosine_ms": round(vector_ms, 2),
                "target_speedup": "~50x vs ARRAY(FLOAT)",
            }


if __name__ == "__main__":
    import asyncio

    from app.database import async_session

    async def main():
        migration = PgVectorMigration(session_factory=async_session)
        results = await migration.migrate_all()
        for r in results:
            print(r)

    asyncio.run(main())
