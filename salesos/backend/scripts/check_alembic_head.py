#!/usr/bin/env python3
"""Fail if Alembic current revision != heads (PROD-W1-002 migrate gate).

Usage (local/docker — full DB check):
  python scripts/check_alembic_head.py
  docker compose exec -T backend python scripts/check_alembic_head.py

Usage (CI — local-only, no DB required):
  python scripts/check_alembic_head.py --local-only

Exit 0 when current matches all heads; exit 1 on drift or error.
Never runs upgrade/downgrade. Never targets production by itself.

--local-only mode verifies the migration chain is healthy (single head,
no branching) without a DB connection.  DB-vs-repo sync is enforced at
deploy time by ``alembic upgrade head`` (railway.json preDeployCommand).
"""
from __future__ import annotations

import argparse
import asyncio
import sys


async def _get_current_heads(database_url: str) -> set[str]:
    from alembic.runtime.migration import MigrationContext
    from sqlalchemy.ext.asyncio import create_async_engine

    engine = create_async_engine(database_url)

    def _read(sync_conn):
        context = MigrationContext.configure(sync_conn)
        return set(context.get_current_heads())

    try:
        async with engine.connect() as conn:
            return await conn.run_sync(_read)
    finally:
        await engine.dispose()


def _get_repo_heads() -> set[str]:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    return set(script.get_heads())


def _check_local_only() -> int:
    heads = _get_repo_heads()
    print(f"alembic heads: {sorted(heads)}")

    if len(heads) == 0:
        print("FAIL: no alembic heads found — broken migration chain", file=sys.stderr)
        return 1
    if len(heads) > 1:
        print(
            f"FAIL: {len(heads)} heads found — merge before deploying",
            file=sys.stderr,
        )
        return 1

    print(f"OK: single head = {sorted(heads)[0]}")
    return 0


def _check_with_db() -> int:
    from app.config import settings

    heads = _get_repo_heads()
    current = asyncio.run(_get_current_heads(settings.resolved_database_url))

    print(f"alembic current: {sorted(current) or ['(none)']}")
    print(f"alembic heads:   {sorted(heads)}")

    if current != heads:
        print(
            "FAIL: schema drift - run `alembic upgrade head` on a non-prod copy before traffic.",
            file=sys.stderr,
        )
        return 1

    print("OK: alembic current == heads")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--local-only",
        action="store_true",
        help="Skip DB connection; verify migration chain is healthy (single head).",
    )
    args = parser.parse_args()

    if args.local_only:
        return _check_local_only()
    return _check_with_db()


if __name__ == "__main__":
    raise SystemExit(main())
