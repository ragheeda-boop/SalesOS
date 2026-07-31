"""Sprint 04 Story 4.3: Verify get_db() uses app engine, not owner engine.
Owner engine (salesos) is superuser/BYPASSRLS — if any request path
accidentally uses it, RLS is silently bypassed.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.database import get_db


@pytest.mark.asyncio
async def test_get_db_yields_app_engine_session():
    """Verify get_db() yields a session connected as salesos_app."""
    async for session in get_db():
        result = await session.execute(text("SELECT current_user"))
        user = result.scalar()
        assert user == "salesos_app", (
            f"get_db() session is '{user}', expected 'salesos_app'. "
            f"Owner engine leak would silently bypass RLS."
        )
        await session.rollback()
        break


@pytest.mark.asyncio
async def test_owner_engine_not_imported_by_request_paths():
    """Verify no route or middleware imports owner_engine directly."""
    import os

    violations: list[str] = []
    app_dir = os.path.join(os.path.dirname(__file__), "..", "app")
    for root, _dirs, files in os.walk(app_dir):
        for f in files:
            if f.endswith(".py") and "test" not in root and "alembic" not in root:
                path = os.path.join(root, f)
                with open(path, encoding="utf-8") as fh:
                    content = fh.read()
                if "owner_engine" in content and "from app.database import" in content:
                    violations.append(path.replace(app_dir + "/", ""))

    assert len(violations) == 0, (
        f"owner_engine imported outside database.py/alembic: {violations}. "
        f"Request-serving code must use get_db() → engine (salesos_app), not owner_engine."
    )
