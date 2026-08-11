"""
Agent Runtime Celery tasks.

Registered via celery_app.include:
  - agent_dispatch_all: triggered by Celery Beat every 60 seconds
"""
from __future__ import annotations

import asyncio
import logging

from celery import shared_task

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Bridge sync Celery tasks to async via a fresh event loop.

    Prefer asyncio.run over the deprecated event-loop getter: Celery prefork
    MainThread on Python 3.10+ has no current loop, which raises RuntimeError.

    Callers that use module-level AsyncEngine (app.database.engine) MUST
    dispose that engine on the same loop before asyncio.run returns —
    otherwise the next Celery tick hits 'Future attached to a different
    loop' (same class as employee _engine / probe_login_tenant_id).
    """
    return asyncio.run(coro)


@shared_task(
    name="agent_dispatch_all",
    bind=True,
    max_retries=0,
    default_retry_delay=60,
    soft_time_limit=110,
    time_limit=120,
)
def agent_dispatch_all(self) -> dict:
    async def _dispatch() -> dict:
        from app.database import async_session, engine

        stats = {"tenants_processed": 0, "tasks_claimed": 0, "errors": []}

        try:
            from sqlalchemy import text

            try:
                async with async_session() as session:
                    result = await session.execute(
                        text("SELECT id FROM tenants WHERE status = 'active' LIMIT 100")
                    )
                    tenant_rows = result.fetchall()

                for row in tenant_rows:
                    tid = str(row.id)
                    try:
                        from runtime.agent_runtime.dispatcher import dispatch_all

                        result = await dispatch_all(tid)
                        stats["tenants_processed"] += 1
                        stats["tasks_claimed"] += (
                            result.get("claimed_fast", 0)
                            + result.get("claimed_research", 0)
                        )
                        if result.get("errors"):
                            stats["errors"].extend(result["errors"])
                    except Exception as e:
                        logger.warning(f"Agent dispatch failed for tenant {tid}: {e}")
                        stats["errors"].append(str(e))
            except Exception as e:
                logger.warning(f"Agent dispatch load tenants failed: {e}")
                stats["errors"].append(str(e))

            return stats
        finally:
            # Same-loop dispose before asyncio.run closes the loop.
            # Prevents pool connections from surviving into the next tick.
            try:
                await engine.dispose()
            except Exception:
                logger.warning(
                    "agent_dispatch_all engine.dispose failed",
                    exc_info=True,
                )

    try:
        return _run_async(_dispatch())
    except Exception as e:
        logger.exception("Agent dispatch fatal error")
        return {"error": str(e)}
