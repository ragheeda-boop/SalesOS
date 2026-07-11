"""Workflow engine — executes workflows with step handlers, conditions, and logging."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import Workflow, WorkflowExecution, WorkflowExecutionStep, WorkflowStep

logger = logging.getLogger(__name__)


def _eval_condition(condition: str, context: dict[str, Any]) -> bool:
    """Simple expression evaluator for step conditions.

    Supports: ``var == val``, ``var != val``, ``var > val``, ``var < val``,
    ``var >= val``, ``var <= val``, ``var in [a,b]``, ``var not in [a,b]``.
    Uses dot-notation for nested context (e.g. ``context.deal.amount``).
    """
    if not condition or not condition.strip():
        return True

    expr = condition.strip()

    def _resolve(path: str, ctx: dict) -> Any:
        key = path.removeprefix("context.")
        parts = key.split(".")
        val: Any = ctx
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p, "")
            else:
                val = getattr(val, p, "")
        return val

    operators = [
        (" not in ", lambda a, b: _resolve(a, context) not in _parse_list(b)),
        (" in ", lambda a, b: _resolve(a, context) in _parse_list(b)),
        (" >= ", lambda a, b: _resolve(a, context) >= _to_num(b)),
        (" <= ", lambda a, b: _resolve(a, context) <= _to_num(b)),
        (" != ", lambda a, b: str(_resolve(a, context)) != _strip_quotes(b)),
        (" == ", lambda a, b: str(_resolve(a, context)) == _strip_quotes(b)),
        (" > ", lambda a, b: float(_resolve(a, context)) > float(b)),
        (" < ", lambda a, b: float(_resolve(a, context)) < float(b)),
    ]

    for op, fn in operators:
        if op in expr:
            parts = expr.split(op, 1)
            return fn(parts[0].strip(), parts[1].strip())

    logger.warning("Could not parse condition: %s — defaulting to True", condition)
    return True


def _parse_list(raw: str) -> list[str]:
    raw = raw.strip().strip("[]").strip()
    if not raw:
        return []
    return [x.strip().strip("'\"") for x in raw.split(",")]


def _to_num(raw: str) -> float | int:
    try:
        return int(raw)
    except ValueError:
        return float(raw)


def _strip_quotes(raw: str) -> str:
    return raw.strip().strip("'\"")


class WorkflowEngine:
    """Executes workflows, handling each step with built-in step handlers."""

    def __init__(self, repository: Any) -> None:
        self._repo = repository
        self._step_handlers: dict[str, Any] = {
            "send_email": self._handle_send_email,
            "update_crm": self._handle_update_crm,
            "create_task": self._handle_create_task,
            "webhook": self._handle_webhook,
            "nba_recommend": self._handle_nba_recommend,
        }
        self._max_retries = 2
        self._retry_delay = 0.0  # seconds

    def register_handler(self, step_type: str, handler: Any) -> None:
        self._step_handlers[step_type] = handler

    async def execute(self, workflow: Workflow, context: dict[str, Any]) -> WorkflowExecution:
        execution = WorkflowExecution(
            id=f"exec_{workflow.id}_{datetime.now(timezone.utc).timestamp()}",
            workflow_id=workflow.id,
            tenant_id=workflow.tenant_id,
            trigger_event=context.get("trigger", "manual"),
        )
        await self._repo.create_execution(execution)

        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)

        for step in sorted_steps:
            step_result = await self._execute_step(step, context)
            execution.step_results.append(step_result)

            if step_result.status == "failed":
                execution.status = "failed"
                execution.error = f"Step '{step.step_type}' (order {step.order}) failed: {step_result.error}"
                execution.completed_at = datetime.now(timezone.utc)
                await self._repo.update_execution(execution)
                return execution

        execution.status = "completed"
        execution.completed_at = datetime.now(timezone.utc)
        await self._repo.update_execution(execution)
        return execution

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]) -> WorkflowExecutionStep:
        step_result = WorkflowExecutionStep(
            id=f"step_{step.id}_{datetime.now(timezone.utc).timestamp()}",
            execution_id="",
            step_id=step.id,
            step_type=step.step_type,
        )

        if not _eval_condition(step.condition, context):
            step_result.status = "skipped"
            step_result.result = {"skipped": True, "reason": f"condition '{step.condition}' evaluated to False"}
            step_result.completed_at = datetime.now(timezone.utc)
            return step_result

        handler = self._step_handlers.get(step.step_type)
        if not handler:
            step_result.status = "failed"
            step_result.error = f"No handler registered for step_type '{step.step_type}'"
            step_result.completed_at = datetime.now(timezone.utc)
            return step_result

        step_result.started_at = datetime.now(timezone.utc)
        last_error: str | None = None

        for attempt in range(1, self._max_retries + 1):
            try:
                result = await handler(step.config, context)
                step_result.status = "completed"
                step_result.result = result
                step_result.completed_at = datetime.now(timezone.utc)
                return step_result
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Step %s attempt %d failed: %s", step.id, attempt, exc)
                if attempt < self._max_retries:
                    import asyncio
                    await asyncio.sleep(self._retry_delay)

        step_result.status = "failed"
        step_result.error = last_error
        step_result.completed_at = datetime.now(timezone.utc)
        return step_result

    async def _handle_send_email(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        to = _resolve_config(config.get("to", ""), context)
        subject = _resolve_config(config.get("subject", ""), context)
        body = _resolve_config(config.get("body", ""), context)
        logger.info("Sending email to=%s subject=%s", to, subject)
        if not to:
            raise ValueError("send_email: 'to' address is required")
        return {"to": to, "subject": subject, "body_preview": body[:100] if body else "", "sent": True}

    async def _handle_update_crm(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        entity = config.get("entity", "")
        entity_id = _resolve_config(str(config.get("entity_id", "")), context)
        fields = config.get("fields", {})
        logger.info("Updating CRM %s %s with %s", entity, entity_id, fields)
        if not entity_id:
            raise ValueError("update_crm: 'entity_id' is required")
        return {"entity": entity, "entity_id": entity_id, "fields": fields, "updated": True}

    async def _handle_create_task(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        title = _resolve_config(config.get("title", ""), context)
        assignee = _resolve_config(config.get("assignee", ""), context)
        description = _resolve_config(config.get("description", ""), context)
        logger.info("Creating task title=%s assignee=%s", title, assignee)
        if not title:
            raise ValueError("create_task: 'title' is required")
        return {"title": title, "assignee": assignee, "description": description, "created": True}

    async def _handle_webhook(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        url = _resolve_config(config.get("url", ""), context)
        method = config.get("method", "POST")
        logger.info("Calling webhook url=%s method=%s", url, method)
        if not url:
            raise ValueError("webhook: 'url' is required")
        return {"url": url, "method": method, "status_code": 200, "called": True}

    async def _handle_nba_recommend(self, config: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        action = config.get("action", "")
        reason = _resolve_config(config.get("reason", ""), context)
        logger.info("NBA recommend action=%s reason=%s", action, reason)
        return {"action": action, "reason": reason, "recommended": True}


def _resolve_config(value: str | Any, context: dict[str, Any]) -> Any:
    """Resolve ``{{context.key}}`` placeholders in config values."""
    if not isinstance(value, str):
        return value
    def _replacer(m: re.Match) -> str:
        key = m.group(1).strip()
        if key.startswith("context."):
            key = key[8:]
        return str(context.get(key, m.group(0)))
    return re.sub(r"\{\{([^}]+)\}\}", _replacer, value)
