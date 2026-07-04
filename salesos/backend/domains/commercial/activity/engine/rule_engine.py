"""ActivityRuleEngine — maps Activity outcomes to Pipeline progression.

This is the bridge between Activity Domain and Pipeline Domain.
Activity never imports Pipeline. The Rule Engine coordinates them.
"""

from __future__ import annotations

from typing import Any, Callable

from ..contracts.models import ActivityOutcome


class ActivityRuleEngine:
    """Evaluates activity outcomes and triggers business actions.

    Rules are registered externally (e.g., by PipelineService).
    The Rule Engine knows nothing about Pipeline — it executes registered rules.
    """

    def __init__(self):
        self._rules: dict[str, list[Callable]] = {}

    def on_outcome(self, business_action: str, handler: Callable) -> None:
        """Register a handler for a business action.

        Handler signature: async def handler(outcome: ActivityOutcome) -> None
        """
        if business_action not in self._rules:
            self._rules[business_action] = []
        self._rules[business_action].append(handler)

    async def evaluate(self, outcome: ActivityOutcome) -> list[str]:
        """Evaluate an outcome against all registered rules.

        Returns list of actions that were triggered.
        """
        triggered: list[str] = []
        if outcome.business_action in self._rules:
            for handler in self._rules[outcome.business_action]:
                await handler(outcome)
                triggered.append(outcome.business_action)
        return triggered

    @property
    def registered_actions(self) -> list[str]:
        return list(self._rules.keys())
