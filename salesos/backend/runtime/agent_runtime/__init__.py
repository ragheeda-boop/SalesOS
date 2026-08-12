"""
Agent Runtime — durable agent execution orchestrator.

Phase 1: read-only execution of ResearchAgent through existing
GroundingService. Owns execution state (tasks, runs, leases, budgets).
SalesOS owns business state. The two never blur.

Invariants enforced:
  INV-01: Agent Runtime owns execution state. SalesOS owns business state.
  INV-02: No agent accesses domain ORM/repositories directly.
  INV-03: Fencing + idempotency + mutation = one atomic transaction.
  INV-05: Budget spend is fenced against lease_generation.
"""
from __future__ import annotations

import asyncio
import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.database import set_current_tenant_id, reset_current_tenant_id, apply_tenant_guc

from runtime.agent_runtime.models import AgentTask, AgentRun
from runtime.agent_runtime.queue import (
    complete_task as _complete_task,
    fail_task as _fail_task,
)
from runtime.agent_runtime.state_machine import (
    is_valid_transition,
    is_terminal,
    ALL_STATUSES,
    COMPLETION_REASONS,
)
from runtime.agent_runtime.budget import BudgetTracker
from runtime.agent_runtime.preamble import build_preamble

logger = logging.getLogger(__name__)

_agent_runtime_instance = None


def get_agent_runtime() -> "AgentRuntime | None":
    return _agent_runtime_instance


class AgentRuntime:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        self._session_factory = session_factory
        global _agent_runtime_instance
        _agent_runtime_instance = self

    async def run_task(
        self,
        session: AsyncSession,
        task: AgentTask,
        tenant_id: str,
    ) -> dict:
        token = set_current_tenant_id(tenant_id)
        gen = getattr(task, "lease_generation", None)
        try:
            if gen is None:
                logger.error(
                    "run_task refused: missing lease_generation task_id=%s",
                    getattr(task, "id", None),
                )
                return {"status": "FAILED", "error": "missing lease_generation"}
            return await self._run_task_internal(session, task, tenant_id, int(gen))
        finally:
            reset_current_tenant_id(token)

    async def _run_task_internal(
        self,
        session: AsyncSession,
        task: AgentTask,
        tenant_id: str,
        lease_generation: int,
    ) -> dict:
        task_id = str(task.id)
        kind = getattr(task, 'kind', 'unknown')
        # set_config(..., is_local=true) dies on COMMIT — pin before every txn.
        await apply_tenant_guc(session, tenant_id)

        run = AgentRun(
            id=uuid.uuid4(),
            task_id=task.id,
            tenant_id=uuid.UUID(tenant_id),
            agent_type=self._agent_for_kind(kind),
            status="RUNNING",
        )
        session.add(run)

        transition = await session.execute(
            text("""
                UPDATE agent_tasks SET status = 'RUNNING', session_id = :sid, updated_at = :now
                WHERE id = :tid AND status = 'CLAIMED'
                AND lease_generation = :gen
            """),
            {
                "tid": task_id,
                "sid": str(run.id),
                "now": datetime.now(timezone.utc),
                "gen": lease_generation,
            },
        )
        if transition.rowcount == 0:
            # Stale lease / recover raced us — never execute the agent.
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            run.result_summary = "CLAIMED→RUNNING fence rejected"
            await session.commit()
            logger.warning(
                "CLAIMED→RUNNING fence rejected task_id=%s gen=%s",
                task_id,
                lease_generation,
            )
            return {"status": "STALE", "error": "CLAIMED→RUNNING fence rejected"}

        await session.commit()
        await apply_tenant_guc(session, tenant_id)

        budget = BudgetTracker(session, str(run.id), task_id,
                               budget=task.budget, lease_generation=lease_generation)

        preamble = await build_preamble(session, task, tenant_id)

        try:
            agent_start = datetime.now(timezone.utc)

            result = await self._execute_agent(task, tenant_id, preamble)

            duration_ms = (datetime.now(timezone.utc) - agent_start).total_seconds() * 1000

            outcome = result.get("output", {}).get("analysis", "Task completed.") if result.get("output") else "Task completed."

            await _complete_task(
                session, task_id, str(outcome)[:1000],
                completion_reason="SUCCESS",
                lease_generation=lease_generation,
            )

            await session.execute(
                text("""
                    UPDATE agent_runs
                    SET status = 'COMPLETED', completed_at = :now,
                        result_summary = :summary, result_data = :data
                    WHERE id = :rid
                """),
                {"rid": str(run.id), "now": datetime.now(timezone.utc),
                 "summary": str(outcome)[:1000], "data": f'{{"duration_ms": {duration_ms}}}'},
            )
            await session.commit()

            return {"status": "COMPLETED", "outcome": str(outcome)[:500]}

        except Exception as e:
            logger.exception(f"Agent execution failed for task {task_id}")
            await _fail_task(session, task_id, str(e)[:1000], lease_generation=lease_generation)

            await session.execute(
                text("""
                    UPDATE agent_runs SET status = 'FAILED', completed_at = :now,
                        result_summary = :error WHERE id = :rid
                """),
                {"rid": str(run.id), "now": datetime.now(timezone.utc), "error": str(e)[:1000]},
            )
            await session.commit()

            return {"status": "FAILED", "error": str(e)[:500]}

    async def _execute_agent(self, task: AgentTask, tenant_id: str, preamble: str) -> dict:
        kind = getattr(task, 'kind', 'unknown')

        if kind in ("research_company", "recheck", "company_profile", "identify"):
            return await self._run_research_agent(task, tenant_id)

        return {"output": {"analysis": f"No handler for task kind: {kind}"}}

    async def _run_research_agent(self, task: AgentTask, tenant_id: str) -> dict:
        from intelligence.agents.base import AgentTask as LibAgentTask, AgentResult
        from intelligence.agent_base import GroundedBaseAgent
        from intelligence.agents.research import ResearchAgent
        from intelligence.grounding import GroundingService
        from intelligence.agents.llm import LLMService

        company_id = task.input_data.get("company_id") or (str(task.entity_id) if task.entity_id else None)
        if not company_id:
            return {"output": {"analysis": "No company_id provided for research."}}

        agent_task = LibAgentTask(
            id=str(task.id),
            agent_type="ResearchAgent",
            input={"company_id": company_id, "tenant_id": tenant_id},
        )

        from app.database import async_session as asf

        # Nested Grounding sessions must pin GUC; ContextVar alone is not enough
        # under FORCE RLS (IL-2B.2 tenant isolation).
        grounding = GroundingService(
            db_session_factory=_tenant_scoped_session_factory(asf, tenant_id),
        )
        llm = LLMService()

        agent = ResearchAgent(llm=llm)
        agent._grounding = grounding

        agent_result: AgentResult = await agent.execute_grounded(agent_task)

        return {
            "output": agent_result.output,
            "confidence": agent_result.confidence,
            "success": agent_result.success,
        }

    @staticmethod
    def _agent_for_kind(kind: str) -> str:
        mapping = {
            "research_company": "ResearchAgent",
            "assess_icp": "ResearchAgent",
            "investigate_expansion": "ResearchAgent",
            "verify_license": "ResearchAgent",
            "stagnation_alert": "ResearchAgent",
            "executive_change": "RelationshipAgent",
            "brand": "DirectHandler",
            "portrait": "DirectHandler",
        }
        return mapping.get(kind, "ResearchAgent")

    async def close(self) -> None:
        pass


class _TenantScopedSessionFactory:
    """Wrap async_session so every nested session applies tenant GUC."""

    def __init__(self, base_factory, tenant_id: str):
        self._base = base_factory
        self._tenant_id = tenant_id

    def __call__(self):
        return _TenantScopedSessionCM(self._base(), self._tenant_id)


class _TenantScopedSessionCM:
    def __init__(self, inner_cm, tenant_id: str):
        self._inner = inner_cm
        self._tenant_id = tenant_id

    async def __aenter__(self):
        session = await self._inner.__aenter__()
        await apply_tenant_guc(session, self._tenant_id)
        return session

    async def __aexit__(self, exc_type, exc, tb):
        return await self._inner.__aexit__(exc_type, exc, tb)


def _tenant_scoped_session_factory(base_factory, tenant_id: str):
    return _TenantScopedSessionFactory(base_factory, tenant_id)
