"""sync_notion_database() (app/tasks.py) never pinned the tenant GUC before
constructing NotionSyncService, despite already receiving tenant_id as a
plain task parameter -- the easy case (see test_tasks_guc_and_column_db.py's
module docstring for the full finding, including the harder, undecided
architecture gap in _get_entity_tenant()'s callers).

Isolated into its own file/process on purpose: `sync_notion_database` is a
bound Celery task whose body calls `asyncio.run()` internally to bridge into
async code -- nesting that inside pytest-asyncio's own already-running loop
raises "asyncio.run() cannot be called from a running event loop", and the
module-level `app.database.engine`'s connection pool is loop-bound (asyncpg)
-- reusing it after any other async test in the same process leaves stale,
now-wrong-loop connections that raise "attached to a different loop" the
moment this task's own fresh loop touches the pool. Running this file alone
means no prior async test has ever established a connection under a
different loop.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text


def test_sync_notion_database_pins_the_guc_before_import(monkeypatch):
    """Discriminating proof: patch NotionSyncService.import_companies to
    capture the session it receives and assert app.tenant_id is actually
    set on that session's connection -- proving the pin is applied, not
    just that the call didn't crash."""
    import app.modules.notion_sync.service as notion_service_mod
    from app.tasks import sync_notion_database

    tenant_id = str(uuid.uuid4())
    captured: dict = {}

    class _FakeService:
        def __init__(self, db):
            captured["db"] = db

        async def import_companies(self, database_id, token, tid):
            result = await captured["db"].execute(
                text("SELECT current_setting('app.tenant_id', true)")
            )
            captured["pinned_tenant_id"] = result.scalar()

    monkeypatch.setattr(notion_service_mod, "NotionSyncService", _FakeService)
    monkeypatch.setattr("app.config.settings.notion_token", "fake-token")

    # Calling a bound Celery task object directly runs it synchronously,
    # with `self` (the Task instance) supplied automatically by Celery.
    sync_notion_database("db-1", tenant_id)

    assert captured.get("pinned_tenant_id") == tenant_id
