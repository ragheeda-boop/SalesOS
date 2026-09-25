#!/usr/bin/env python3
"""Compare every SQLAlchemy ORM table definition with a migrated database.

Reports tables and columns an ORM model declares but the database lacks, and
columns whose type family differs. Such drift surfaces at runtime as
UndefinedColumn / DatatypeMismatch on paths no test exercises (reports 70–98).
Read-only: it only queries information_schema.

Point it ONLY at a disposable database migrated to head:

    python scripts/audit_orm_schema_drift.py --dsn postgresql://postgres:pw@host:5432/scratch_db
"""

from __future__ import annotations

import argparse
import asyncio
import gc
import json
import sys

import asyncpg
from sqlalchemy import MetaData

# Type families: ORM visit name / compiled prefix -> accepted information_schema data_type values.
FAMILIES = {
    "uuid": {"uuid"},
    "string": {"character varying", "text", "character", "uuid", "USER-DEFINED"},
    "text": {"text", "character varying"},
    "integer": {"integer", "bigint", "smallint"},
    "biginteger": {"bigint", "integer"},
    "smallinteger": {"smallint", "integer"},
    "boolean": {"boolean"},
    "float": {"double precision", "real", "numeric"},
    "numeric": {"numeric", "double precision", "real"},
    "datetime": {"timestamp with time zone", "timestamp without time zone"},
    "date": {"date"},
    "time": {"time without time zone", "time with time zone"},
    "json": {"json", "jsonb"},
    "jsonb": {"jsonb", "json"},
    "array": {"ARRAY"},
    "enum": {"USER-DEFINED", "character varying", "text"},
    "largebinary": {"bytea"},
    "interval": {"interval"},
    "inet": {"inet"},
}


def _family(col_type) -> str | None:
    name = getattr(col_type, "__visit_name__", "") or type(col_type).__name__
    name = name.lower()
    aliases = {"varchar": "string", "unicode": "string", "unicodetext": "text", "double": "float",
               "double_precision": "float", "real": "float", "timestamp": "datetime",
               "big_integer": "biginteger", "small_integer": "smallinteger", "binary": "largebinary"}
    name = aliases.get(name, name)
    return name if name in FAMILIES else None


def orm_metadata() -> list[MetaData]:
    import app.main  # noqa: F401 — registers routers and, through them, every model
    import app.database  # noqa: F401

    seen, out = set(), []
    for obj in gc.get_objects():
        if isinstance(obj, MetaData) and id(obj) not in seen and obj.tables:
            seen.add(id(obj))
            out.append(obj)
    return out


async def check(dsn: str) -> dict:
    conn = await asyncpg.connect(dsn)
    try:
        rows = await conn.fetch(
            "SELECT table_schema, table_name, column_name, data_type, is_nullable "
            "FROM information_schema.columns WHERE table_schema NOT IN ('pg_catalog','information_schema')"
        )
    finally:
        await conn.close()
    db: dict[tuple[str, str], dict[str, tuple[str, str]]] = {}
    for r in rows:
        db.setdefault((r["table_schema"], r["table_name"]), {})[r["column_name"]] = (
            r["data_type"], r["is_nullable"])

    missing_tables, missing_columns, type_mismatch, unknown_types = [], [], [], set()
    checked_tables = checked_cols = 0
    for md in orm_metadata():
        for table in md.tables.values():
            schema = table.schema or "public"
            if schema in ("pg_catalog", "information_schema"):
                continue  # dialect reflection metadata, not application models
            cols = db.get((schema, table.name))
            checked_tables += 1
            if cols is None:
                missing_tables.append(f"{schema}.{table.name}")
                continue
            for col in table.columns:
                checked_cols += 1
                if col.name not in cols:
                    missing_columns.append(f"{schema}.{table.name}.{col.name}")
                    continue
                fam = _family(col.type)
                if fam is None:
                    unknown_types.add(type(col.type).__name__)
                    continue
                if cols[col.name][0] not in FAMILIES[fam]:
                    type_mismatch.append(
                        f"{schema}.{table.name}.{col.name}: orm={fam} db={cols[col.name][0]}")
    return {
        "tables_checked": checked_tables, "columns_checked": checked_cols,
        "missing_tables": sorted(set(missing_tables)),
        "missing_columns": sorted(set(missing_columns)),
        "type_mismatch": sorted(set(type_mismatch)),
        "unchecked_types": sorted(unknown_types),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dsn", required=True, help="disposable, migrated-to-head database")
    args = parser.parse_args()
    report = asyncio.run(check(args.dsn))
    print(json.dumps(report, indent=2))
    bad = report["missing_tables"] or report["missing_columns"] or report["type_mismatch"]
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
