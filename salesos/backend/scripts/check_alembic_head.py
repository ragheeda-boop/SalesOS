#!/usr/bin/env python3
"""Fail if Alembic current revision != heads (PROD-W1-002 migrate gate).

Usage (local/docker):
  python scripts/check_alembic_head.py
  docker compose exec -T backend python scripts/check_alembic_head.py

Exit 0 when current matches all heads; exit 1 on drift or error.
Never runs upgrade/downgrade. Never targets production by itself.
"""
from __future__ import annotations

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


def main() -> int:
    from alembic.config import Config
    from alembic.script import ScriptDirectory

    from app.config import settings

    cfg = Config("alembic.ini")
    script = ScriptDirectory.from_config(cfg)
    heads = set(script.get_heads())
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


if __name__ == "__main__":
    raise SystemExit(main())
