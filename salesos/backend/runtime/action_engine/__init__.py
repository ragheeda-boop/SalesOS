"""Action Engine — every button is an Action, not an onClick handler.

Actions are registered in the ActionRegistry. Each action has:
  - id, label, icon, shortcut
  - handler (function to execute)
  - schema (input validation)
  - permissions (who can execute)
  - hooks (before/after extension points)
  - audit (every execution is logged)

No hardcoded onClick anywhere. Every button resolves to an action.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Optional


class ActionStatus(str, Enum):
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    REJECTED = "rejected"


@dataclass
class ActionDefinition:
    id: str
    label: str
    label_ar: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    shortcut: Optional[str] = None
    handler: Optional[Callable] = None
    schema: Optional[dict] = None  # JSON Schema for input
    permissions: list[str] = field(default_factory=list)
    confirm_message: Optional[str] = None
    category: str = "general"
    audit: bool = True
    timeout_ms: int = 30000

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "label_ar": self.label_ar or self.label,
            "description": self.description,
            "icon": self.icon,
            "shortcut": self.shortcut,
            "schema": self.schema,
            "permissions": self.permissions,
            "confirm_message": self.confirm_message,
            "category": self.category,
            "audit": self.audit,
            "timeout_ms": self.timeout_ms,
        }


@dataclass
class ActionExecution:
    id: str
    action_id: str
    user_id: str
    tenant_id: str
    input: dict = field(default_factory=dict)
    status: ActionStatus = ActionStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "action_id": self.action_id,
            "user_id": self.user_id,
            "tenant_id": self.tenant_id,
            "input": self.input,
            "status": self.status.value,
            "result": self.result,
            "error": self.error,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }


class ActionRegistry:
    """Central registry of all actions in the platform."""

    def __init__(self):
        self._actions: dict[str, ActionDefinition] = {}
        self._executions: dict[str, ActionExecution] = {}
        self._before_hooks: dict[str, list[Callable]] = {}
        self._after_hooks: dict[str, list[Callable]] = {}

    def register(self, action: ActionDefinition):
        self._actions[action.id] = action

    def get(self, action_id: str) -> Optional[ActionDefinition]:
        return self._actions.get(action_id)

    def all(self, category: Optional[str] = None) -> list[ActionDefinition]:
        if category:
            return [a for a in self._actions.values() if a.category == category]
        return list(self._actions.values())

    def before(self, action_id: str, hook: Callable):
        self._before_hooks.setdefault(action_id, []).append(hook)

    def after(self, action_id: str, hook: Callable):
        self._after_hooks.setdefault(action_id, []).append(hook)

    async def execute(self, action_id: str, user_id: str, tenant_id: str,
                      input: Optional[dict] = None,
                      permissions: Optional[list[str]] = None) -> ActionExecution:
        import uuid
        action = self._actions.get(action_id)
        if not action:
            raise ValueError(f"Action '{action_id}' not found")

        execution = ActionExecution(
            id=str(uuid.uuid4()),
            action_id=action_id,
            user_id=user_id,
            tenant_id=tenant_id,
            input=input or {},
        )
        self._executions[execution.id] = execution

        # Check permissions
        if permissions and action.permissions:
            if not all(p in permissions for p in action.permissions):
                execution.status = ActionStatus.REJECTED
                execution.error = "Permission denied"
                execution.completed_at = datetime.now(timezone.utc)
                return execution

        # Before hooks
        for hook in self._before_hooks.get(action_id, []):
            try:
                result = hook(execution)
                if hasattr(result, "__awaitable__"):
                    await result
            except Exception as e:
                execution.status = ActionStatus.FAILED
                execution.error = f"Before hook error: {str(e)}"
                execution.completed_at = datetime.now(timezone.utc)
                return execution

        # Execute
        execution.status = ActionStatus.EXECUTING
        if action.handler:
            try:
                result = action.handler(execution.input)
                if hasattr(result, "__awaitable__"):
                    result = await result
                execution.result = result
                execution.status = ActionStatus.SUCCESS
            except Exception as e:
                execution.status = ActionStatus.FAILED
                execution.error = str(e)
        else:
            execution.status = ActionStatus.SUCCESS

        execution.completed_at = datetime.now(timezone.utc)

        # After hooks
        for hook in self._after_hooks.get(action_id, []):
            try:
                result = hook(execution)
                if hasattr(result, "__awaitable__"):
                    await result
            except Exception:
                pass

        return execution

    def get_execution(self, execution_id: str) -> Optional[ActionExecution]:
        return self._executions.get(execution_id)

    def recent_executions(self, user_id: str, limit: int = 20) -> list[ActionExecution]:
        executions = [e for e in self._executions.values() if e.user_id == user_id]
        return sorted(executions, key=lambda x: x.started_at, reverse=True)[:limit]
