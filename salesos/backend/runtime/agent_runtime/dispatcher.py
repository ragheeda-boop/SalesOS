"""
Agent Dispatcher — Celery Beat-triggered task dispatcher.

Dispatch cycle (every 60s):
  1. recoverExpiredLeases() — return orphaned tasks to PENDING
  2. retireExhausted() — mark dead tasks as EXHAUSTED
  3. claimDue() — claim PENDING tasks with FOR UPDATE SKIP LOCKED
  4. dispatch — fast lane (direct) + research lane (LLM session)
"""
from __future__ import annotations

import asyncio
import logging

from app.database import async_session, set_current_tenant_id, reset_current_tenant_id

from runtime.agent_runtime.queue import (
    claim_due as _claim_due,
    recover_expired_leases as _recover_expired_leases,
    retire_exhausted as _retire_exhausted,
    LEASE_MS_FAST,
    LEASE_MS_RESEARCH,
)

logger = logging.getLogger(__name__)

FAST_KINDS = {"brand", "portrait", "simple_lookup"}
RESEARCH_KINDS = {
    "research_company", "assess_icp", "investigate_expansion",
    "executive_change", "verify_license", "stagnation_alert",
    "identify", "profile", "recheck", "meeting_prep",
    "company_profile", "workspace_profile",
}
FAST_BATCH = 60
RESEARCH_BATCH = 12


async def dispatch_all(tenant_id: str) -> dict:
    token = set_current_tenant_id(tenant_id)
    try:
        return await _dispatch_all_internal(tenant_id)
    finally:
        reset_current_tenant_id(token)


async def _dispatch_all_internal(tenant_id: str) -> dict:
    stats = {"recovered": 0, "exhausted": 0, "claimed_fast": 0, "claimed_research": 0, "errors": []}

    try:
        async with async_session() as session:
            stats["recovered"] = await _recover_expired_leases(session, tenant_id)
            stats["exhausted"] = await _retire_exhausted(session, tenant_id)
            await session.commit()
    except Exception as e:
        logger.warning(f"Pre-dispatch cleanup failed: {e}")
        stats["errors"].append(str(e))
        return stats

    try:
        async with async_session() as session:
            fast_tasks = await _claim_due(
                session, tenant_id, limit=FAST_BATCH,
                kinds_include=list(FAST_KINDS), lease_ms=LEASE_MS_FAST,
            )
            await session.commit()
            stats["claimed_fast"] = len(fast_tasks)
    except Exception as e:
        logger.warning(f"Fast lane claim failed: {e}")
        stats["errors"].append(str(e))

    try:
        async with async_session() as session:
            research_tasks = await _claim_due(
                session, tenant_id, limit=RESEARCH_BATCH,
                kinds_exclude=list(FAST_KINDS), lease_ms=LEASE_MS_RESEARCH,
            )
            await session.commit()
            stats["claimed_research"] = len(research_tasks)
    except Exception as e:
        logger.warning(f"Research lane claim failed: {e}")
        stats["errors"].append(str(e))

    if stats["claimed_fast"] > 0:
        agents = []
        for _ in range(min(6, stats["claimed_fast"])):
            agents.append(_call_fast_handler(tenant_id))
        await asyncio.gather(*agents, return_exceptions=True)

    if stats["claimed_research"] > 0:
        agents = []
        for _ in range(min(12, stats["claimed_research"])):
            agents.append(_call_research_handler(tenant_id))
        await asyncio.gather(*agents, return_exceptions=True)

    return stats


async def _call_fast_handler(tenant_id: str) -> None:
    try:
        from runtime.agent_runtime import AgentRuntime
        runtime = AgentRuntime(async_session)
        async with async_session() as session:
            tasks = await _claim_due(session, tenant_id, limit=1,
                                     kinds_include=list(FAST_KINDS), lease_ms=LEASE_MS_FAST)
            await session.commit()
            if tasks:
                await runtime.run_task(session, tasks[0], tenant_id)
    except Exception as e:
        logger.warning(f"Fast handler failed: {e}")


async def _call_research_handler(tenant_id: str) -> None:
    try:
        from runtime.agent_runtime import AgentRuntime
        runtime = AgentRuntime(async_session)
        async with async_session() as session:
            tasks = await _claim_due(session, tenant_id, limit=1,
                                     kinds_exclude=list(FAST_KINDS), lease_ms=LEASE_MS_RESEARCH)
            await session.commit()
            if tasks:
                await runtime.run_task(session, tasks[0], tenant_id)
    except Exception as e:
        logger.warning(f"Research handler failed: {e}")
