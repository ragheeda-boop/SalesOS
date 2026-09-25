#!/usr/bin/env python3
"""Plan every static ``text("...")`` SQL statement in the backend against a
fully migrated database, and report the ones PostgreSQL cannot plan.

Catches wrong table/column names, uuid/varchar comparisons and malformed SQL
in code paths no test exercises. EXPLAIN never executes a statement, and each
one runs in a transaction that is rolled back.

Point it ONLY at a disposable database migrated to head:

    python scripts/audit_sql_explain_sweep.py --dsn postgresql://postgres:pw@host:5432/scratch_db

Known limits: dynamic SQL (f-strings) is skipped; binds are replaced with NULL,
so an expanding bind such as ``IN :ids`` reports a false syntax error.
"""

from __future__ import annotations

import argparse
import ast
import asyncio
import json
import re
import sys
from pathlib import Path

import asyncpg

ROOT = Path(__file__).resolve().parents[1]
DIRS = ("app", "runtime", "domains", "intelligence", "sdk")
BIND = re.compile(r"(?<![:\w]):([A-Za-z_]\w*)(?!\w)")
HEADS = ("SELECT", "WITH", "INSERT", "UPDATE", "DELETE")


def statements():
    for d in DIRS:
        for path in (ROOT / d).rglob("*.py"):
            if {"tests", "alembic", "__pycache__"} & set(path.parts):
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8"))
            except (SyntaxError, UnicodeDecodeError):
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call) or not node.args:
                    continue
                fn = node.func
                name = fn.id if isinstance(fn, ast.Name) else getattr(fn, "attr", "")
                arg = node.args[0]
                if name not in ("text", "sa_text") or not isinstance(arg, ast.Constant) \
                        or not isinstance(arg.value, str):
                    continue
                sql = arg.value.strip().rstrip(";")
                if not sql or sql.split(None, 1)[0].upper() not in HEADS:
                    continue
                yield str(path.relative_to(ROOT)), node.lineno, BIND.sub("NULL", sql)


async def sweep(dsn: str) -> list[dict]:
    conn = await asyncpg.connect(dsn)
    failures = []
    try:
        for file, line, sql in statements():
            tr = conn.transaction()
            await tr.start()
            try:
                await conn.execute("EXPLAIN " + sql)
            except Exception as exc:  # noqa: BLE001 - every planning failure is a finding
                failures.append({"file": file, "line": line,
                                 "error": f"{type(exc).__name__}: {str(exc).splitlines()[0]}"})
            finally:
                await tr.rollback()
    finally:
        await conn.close()
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--dsn", required=True, help="disposable, migrated-to-head database")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    failures = asyncio.run(sweep(args.dsn))
    if args.json:
        print(json.dumps(failures, indent=2))
    else:
        for f in failures:
            print(f"{f['file']}:{f['line']}  {f['error']}")
        print(f"\n{len(failures)} statement(s) failed to plan")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
