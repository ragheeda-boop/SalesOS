"""
Agent Dispatcher — Celery Beat-triggered task dispatcher.

Dispatch cycle (every 60s):
  1. recoverExpiredLeases() — return orphaned tasks to PENDING
  2. retireExhausted() — mark dead tasks as EXHAUSTED
  3. claimDue() — claim PENDING tasks with FOR UPDATE SKIP LOCKED
  4. dispatch — fast lane (direct) + research lane (LLM session)

RLS: salesos_app has FORCE RLS on agent_tasks. Every session used for
claim/recover/retire/run must pin app.tenant_id via apply_tenant_guc
(ContextVar alone does not set the GUC).
"""
from __future__ import annotations

import asyncio
import logging

from app.database import (
    async_session,
    set_current_tenant_id,
    reset_current_tenant_id,
    apply_tenant_guc,
)

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
FAST_CONCURRENCY = 6
RESEARCH_CONCURRENCY = 12


async def dispatch_all(tenant_id: str) -> dict:
    token = set_current_tenant_id(tenant_id)
    try:
        return await _dispatch_all_internal(tenant_id)
    finally:
        reset_current_tenant_id(token)


async def _dispatch_all_internal(tenant_id: str) -> dict:
    stats = {"recovered": 0, "exhausted": 0, "claimed_fast": 0, "claimed_research": 0, "errors": []}
    fast_tasks: list = []
    research_tasks: list = []

    try:
        async with async_session() as session:
            await apply_tenant_guc(session, tenant_id)
            stats["recovered"] = await _recover_expired_leases(session, tenant_id)
            stats["exhausted"] = await _retire_exhausted(session, tenant_id)
            await session.commit()
    except Exception as e:
        logger.warning(f"Pre-dispatch cleanup failed: {e}")
        stats["errors"].append(str(e))
        return stats

    try:
        async with async_session() as session:
            await apply_tenant_guc(session, tenant_id)
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
            await apply_tenant_guc(session, tenant_id)
            research_tasks = await _claim_due(
                session, tenant_id, limit=RESEARCH_BATCH,
                kinds_include=list(RESEARCH_KINDS), lease_ms=LEASE_MS_RESEARCH,
            )
            await session.commit()
            stats["claimed_research"] = len(research_tasks)
    except Exception as e:
        logger.warning(f"Research lane claim failed: {e}")
        stats["errors"].append(str(e))

    if fast_tasks:
        await _run_claimed_batch(tenant_id, fast_tasks, FAST_CONCURRENCY)
    if research_tasks:
        await _run_claimed_batch(tenant_id, research_tasks, RESEARCH_CONCURRENCY)

    return stats


async def _run_claimed_batch(tenant_id: str, tasks: list, concurrency: int) -> None:
    sem = asyncio.Semaphore(concurrency)

    async def _one(task) -> None:
        async with sem:
            await _run_claimed_task(tenant_id, task)

    await asyncio.gather(*[_one(t) for t in tasks], return_exceptions=True)


async def _run_claimed_task(tenant_id: str, task) -> None:
    """Execute an already-CLAIMED row. Do not claim again."""
    try:
        from runtime.agent_runtime import AgentRuntime
        runtime = AgentRuntime(async_session)
        async with async_session() as session:
            await apply_tenant_guc(session, tenant_id)
            await runtime.run_task(session, task, tenant_id)
    except Exception as e:
        logger.warning(f"Handler failed: {e}")
