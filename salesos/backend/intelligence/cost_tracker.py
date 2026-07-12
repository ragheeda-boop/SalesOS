from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from sdk.config import sdk_settings


MODEL_COST_PER_1K_TOKENS: dict[str, dict[str, float]] = {
    "gpt-4o-mini": {"input": 0.00015, "output": 0.00060},
    "gpt-4o": {"input": 0.0025, "output": 0.010},
    "gpt-4-turbo": {"input": 0.01, "output": 0.03},
    "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
    "text-embedding-3-large": {"input": 0.00013, "output": 0.0},
}

DEFAULT_COST = {"input": 0.001, "output": 0.002}


@dataclass
class CostEstimate:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost: float = 0.0
    model: str = ""


@dataclass
class BudgetEnforcement:
    tenant_id: str
    monthly_budget: float
    current_spend: float = 0.0
    is_exceeded: bool = False


class CostTracker:
    def __init__(self, db_session_factory=None):
        self._db_session_factory = db_session_factory
        self._budgets: dict[str, BudgetEnforcement] = {}

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        rates = MODEL_COST_PER_1K_TOKENS.get(model, DEFAULT_COST)
        input_cost = (prompt_tokens / 1000) * rates["input"]
        output_cost = (completion_tokens / 1000) * rates["output"]
        return round(input_cost + output_cost, 6)

    def track_usage(
        self,
        model: str,
        usage: dict[str, int],
        operation: str = "completion",
        tenant_id: str | None = None,
    ) -> CostEstimate:
        prompt_tokens = usage.get("prompt_tokens", 0)
        completion_tokens = usage.get("completion_tokens", 0)
        total_tokens = usage.get("total_tokens", prompt_tokens + completion_tokens)

        estimated_cost = self.estimate_cost(model, prompt_tokens, completion_tokens)

        if tenant_id:
            self._check_budget(tenant_id, estimated_cost)

        return CostEstimate(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost=estimated_cost,
            model=model,
        )

    def set_budget(self, tenant_id: str, monthly_budget: float):
        current = self._budgets.get(tenant_id)
        if current:
            current.monthly_budget = monthly_budget
        else:
            self._budgets[tenant_id] = BudgetEnforcement(
                tenant_id=tenant_id,
                monthly_budget=monthly_budget,
            )

    def get_spend(self, tenant_id: str) -> float:
        budget = self._budgets.get(tenant_id)
        return budget.current_spend if budget else 0.0

    def _check_budget(self, tenant_id: str, cost: float):
        budget = self._budgets.get(tenant_id)
        if budget:
            budget.current_spend += cost
            if budget.current_spend > budget.monthly_budget:
                budget.is_exceeded = True

    def is_budget_exceeded(self, tenant_id: str) -> bool:
        budget = self._budgets.get(tenant_id)
        return budget.is_exceeded if budget else False
