"""
Agent Runtime Celery tasks.

Registered via celery_app.include:
  - agent_dispatch_all: triggered by Celery Beat every 60 seconds
"""
from __future__ import annotations

import logging
from uuid import uuid4

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    name="agent_dispatch_all",
    bind=True,
    max_retries=0,
    default_retry_delay=60,
    soft_time_limit=110,
    time_limit=120,
)
def agent_dispatch_all(self) -> dict:
    import asyncio

    async def _dispatch() -> dict:
        from sqlalchemy import text
        from app.database import async_session

        stats = {"tenants_processed": 0, "tasks_claimed": 0, "errors": []}

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
                        result.get("claimed_fast", 0) + result.get("claimed_research", 0)
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

    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(_dispatch())
    except Exception as e:
        logger.exception("Agent dispatch fatal error")
        return {"error": str(e)}
