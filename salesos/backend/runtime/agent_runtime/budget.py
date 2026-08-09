"""
Budget Tracker — per-run cost enforcement with fencing.

Source of truth: agent_runs.budget_spent (PostgreSQL).
Process-local cache: contextvar (optimization, not authoritative).

INV-05: Every spend() is fenced against current lease_generation.
"""
from __future__ import annotations

from contextvars import ContextVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

_budget_spent: ContextVar[int] = ContextVar("agent_budget_spent", default=0)
_budget_limit: ContextVar[int] = ContextVar("agent_budget_limit", default=4)
_budget_exhausted: ContextVar[bool] = ContextVar("agent_budget_exhausted", default=False)


class BudgetTracker:
    def __init__(
        self,
        session: AsyncSession,
        run_id: str,
        task_id: str,
        budget: int = 4,
        lease_generation: int | None = None,
    ):
        self._session = session
        self._run_id = run_id
        self._task_id = task_id
        self._budget = budget
        self._lease_generation = lease_generation

        _budget_limit.set(budget)
        _budget_spent.set(0)
        _budget_exhausted.set(False)

    async def load_existing(self) -> int:
        result = await self._session.execute(
            text("SELECT budget_spent FROM agent_runs WHERE id = :rid"),
            {"rid": self._run_id},
        )
        row = result.fetchone()
        if row:
            spent = row.budget_spent
            _budget_spent.set(spent)
            if spent >= self._budget:
                _budget_exhausted.set(True)
            return spent
        return 0

    async def spend(self, units: int = 1) -> dict:
        if _budget_exhausted.get():
            return {"ok": False, "reason": f"Budget exhausted ({_budget_spent.get()}/{self._budget})."}

        from runtime.agent_runtime.queue import LEASE_MS_RESEARCH

        if self._lease_generation is not None:
            result = await self._session.execute(
                text("""
                    UPDATE agent_runs
                    SET budget_spent = budget_spent + :units
                    WHERE id = :run_id
                      AND budget_spent + :units <= :budget
                      AND EXISTS (
                          SELECT 1 FROM agent_tasks
                          WHERE id = :task_id
                            AND lease_generation = :gen
                            AND status = 'RUNNING'
                      )
                    RETURNING budget_spent
                """),
                {
                    "run_id": self._run_id, "task_id": self._task_id,
                    "units": units, "budget": self._budget,
                    "gen": self._lease_generation,
                },
            )
        else:
            result = await self._session.execute(
                text("""
                    UPDATE agent_runs
                    SET budget_spent = budget_spent + :units
                    WHERE id = :run_id
                      AND budget_spent + :units <= :budget
                    RETURNING budget_spent
                """),
                {"run_id": self._run_id, "units": units, "budget": self._budget},
            )

        row = result.fetchone()
        if row is None:
            _budget_exhausted.set(True)
            return {"ok": False, "reason": f"Budget exhausted ({_budget_spent.get()}/{self._budget})."}

        _budget_spent.set(row.budget_spent)
        if row.budget_spent >= self._budget:
            _budget_exhausted.set(True)

        return {"ok": True}

    @property
    def budget(self) -> int:
        return self._budget

    @property
    def spent(self) -> int:
        return _budget_spent.get()

    @property
    def exhausted(self) -> bool:
        return _budget_exhausted.get()
