"""Workflow engine — executes workflows with step handlers, conditions, and logging."""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import Workflow, WorkflowExecution, WorkflowExecutionStep, WorkflowStep

try:
    from sdk.events.domain_events import WorkflowCompleted, WorkflowFailed
except ImportError:
    WorkflowCompleted = None
    WorkflowFailed = None

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
    """Executes workflows, handling each step with built-in step handlers.

    Supports:
    - Sequential step execution
    - IF/ELSE conditionals (step_type='if_else')
    - FOR loops (step_type='for_each')
    - Parallel branches (step_type='parallel')
    - Timeouts (step-level and workflow-level)
    - Step state machine: pending → running → completed/failed/timed_out/skipped
    - Domain event emission on completion/failure/timeout
    """

    def __init__(self, repository: Any, event_bus: Any | None = None) -> None:
        self._repo = repository
        self._event_bus = event_bus
        self._step_handlers: dict[str, Any] = {
            "send_email": self._handle_send_email,
            "update_crm": self._handle_update_crm,
            "create_task": self._handle_create_task,
            "webhook": self._handle_webhook,
            "nba_recommend": self._handle_nba_recommend,
            "set_variable": self._handle_set_variable,
            "log_message": self._handle_log_message,
            "if_else": self._handle_if_else,
            "for_each": self._handle_for_each,
            "parallel": self._handle_parallel,
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

        # Check workflow-level timeout
        workflow_timeout = getattr(workflow, "timeout_seconds", None)

        sorted_steps = sorted(workflow.steps, key=lambda s: s.order)

        try:
            if workflow_timeout:
                result = await asyncio.wait_for(
                    self._run_steps(sorted_steps, context, execution),
                    timeout=workflow_timeout,
                )
                if result is None:
                    execution.status = "timed_out"
                    execution.error = f"Workflow timed out after {workflow_timeout}s"
                    execution.completed_at = datetime.now(timezone.utc)
                    await self._repo.update_execution(execution)
                    await self._emit_execution_event(workflow, execution)
                    return execution
            else:
                await self._run_steps(sorted_steps, context, execution)
        except asyncio.TimeoutError:
            execution.status = "timed_out"
            execution.error = f"Workflow timed out after {workflow_timeout}s"
            execution.completed_at = datetime.now(timezone.utc)
            await self._repo.update_execution(execution)
            await self._emit_execution_event(workflow, execution)
            return execution

        if execution.status == "running":
            execution.status = "completed"
            execution.completed_at = datetime.now(timezone.utc)
            await self._repo.update_execution(execution)

        await self._emit_execution_event(workflow, execution)
        return execution

    async def _run_steps(
        self,
        sorted_steps: list[WorkflowStep],
        context: dict[str, Any],
        execution: WorkflowExecution,
    ) -> None:
        for step in sorted_steps:
            step_result = await self._execute_step(step, context)
            execution.step_results.append(step_result)

            if step_result.status == "failed":
                if step.on_failure == "skip":
                    step_result.status = "skipped"
                    step_result.error = None
                elif step.on_failure == "retry":
                    retry_result = await self._execute_step(step, context)
                    if retry_result.status == "failed":
                        execution.status = "failed"
                        execution.error = f"Step '{step.step_type}' (order {step.order}) failed after retry: {step_result.error}"
                        execution.completed_at = datetime.now(timezone.utc)
                        await self._repo.update_execution(execution)
                        return
                else:
                    execution.status = "failed"
                    execution.error = f"Step '{step.step_type}' (order {step.order}) failed: {step_result.error}"
                    execution.completed_at = datetime.now(timezone.utc)
                    await self._repo.update_execution(execution)
                    return

    async def _execute_step(self, step: WorkflowStep, context: dict[str, Any]) -> WorkflowExecutionStep:
        step_result = WorkflowExecutionStep(
            id=f"step_{step.id}_{datetime.now(timezone.utc).timestamp()}",
            execution_id="",
            step_id=step.id,
            step_type=step.step_type,
        )

        # Check condition
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

        step_result.status = "running"
        step_result.started_at = datetime.now(timezone.utc)

        # Execute with optional step-level timeout
        step_timeout = getattr(step, "timeout_seconds", None)
        last_error: str | None = None

        try:
            if step_timeout:
                result = await asyncio.wait_for(
                    self._call_handler(handler, step.config, context, step),
                    timeout=step_timeout,
                )
            else:
                result = await self._call_handler(handler, step.config, context, step)
            step_result.status = "completed"
            step_result.result = result
            step_result.completed_at = datetime.now(timezone.utc)
            return step_result
        except asyncio.TimeoutError:
            step_result.status = "timed_out"
            step_result.error = f"Step timed out after {step_timeout}s"
            step_result.completed_at = datetime.now(timezone.utc)
            return step_result
        except Exception as exc:
            last_error = str(exc)
            logger.warning("Step %s failed: %s", step.id, exc)

        step_result.status = "failed"
        step_result.error = last_error
        step_result.completed_at = datetime.now(timezone.utc)
        return step_result

    async def _call_handler(
        self,
        handler: Any,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep,
    ) -> Any:
        """Call a handler with optional retry logic."""
        last_error: str | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return await handler(config, context, step)
            except Exception as exc:
                last_error = str(exc)
                logger.warning("Step %s attempt %d failed: %s", step.id, attempt, exc)
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_delay)
        raise ValueError(last_error)

    # ── Structural step handlers ───────────────────────────────────────────

    async def _handle_if_else(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep,
    ) -> dict[str, Any]:
        """Handle IF/ELSE conditional step.

        Config:
            condition: str — expression to evaluate
            then_steps: list[dict] — steps to execute if condition is true
            else_steps: list[dict] — steps to execute if condition is false
        """
        condition = config.get("condition", "")
        then_steps = config.get("then_steps", [])
        else_steps = config.get("else_steps", [])

        if _eval_condition(condition, context):
            branch = "then"
            branch_steps = then_steps
        else:
            branch = "else"
            branch_steps = else_steps

        results: list[dict[str, Any]] = []
        for step_def in branch_steps:
            step_type = step_def.get("step_type", "")
            handler = self._step_handlers.get(step_type)
            if handler:
                try:
                    result = await handler(step_def.get("config", {}), context, step)
                    results.append({"step_type": step_type, "result": result, "status": "completed"})
                except Exception as exc:
                    results.append({"step_type": step_type, "error": str(exc), "status": "failed"})
            else:
                results.append({"step_type": step_type, "error": "no handler", "status": "skipped"})

        return {"branch": branch, "condition": condition, "results": results}

    async def _handle_for_each(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep,
    ) -> dict[str, Any]:
        """Handle FOR loop iteration step.

        Config:
            collection_key: str — key in context containing the list to iterate
            item_var: str — variable name to assign each item to
            steps: list[dict] — steps to execute for each item
        """
        collection_key = config.get("collection_key", "")
        item_var = config.get("item_var", "item")
        steps_defs = config.get("steps", [])

        collection = context.get(collection_key, [])
        if not isinstance(collection, list):
            collection = [collection]

        results: list[dict[str, Any]] = []
        for idx, item in enumerate(collection):
            loop_context = {**context, item_var: item, f"{item_var}_index": idx}
            for step_def in steps_defs:
                step_type = step_def.get("step_type", "")
                handler = self._step_handlers.get(step_type)
                if handler:
                    try:
                        result = await handler(step_def.get("config", {}), loop_context, step)
                        results.append({
                            "index": idx,
                            "step_type": step_type,
                            "result": result,
                            "status": "completed",
                        })
                    except Exception as exc:
                        results.append({
                            "index": idx,
                            "step_type": step_type,
                            "error": str(exc),
                            "status": "failed",
                        })

        return {"collection_key": collection_key, "iterations": len(collection), "results": results}

    async def _handle_parallel(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep,
    ) -> dict[str, Any]:
        """Handle parallel branch execution — all branches run concurrently.

        Config:
            branches: list[list[dict]] — list of branch step-lists
            max_concurrency: int — max concurrent branches (default: 10)
        """
        branches = config.get("branches", [])
        max_concurrency = config.get("max_concurrency", 10)

        semaphore = asyncio.Semaphore(max_concurrency)

        async def _run_branch(branch_steps: list[dict], branch_idx: int) -> dict[str, Any]:
            async with semaphore:
                branch_results: list[dict[str, Any]] = []
                branch_status = "completed"
                for step_def in branch_steps:
                    step_type = step_def.get("step_type", "")
                    handler = self._step_handlers.get(step_type)
                    if handler:
                        try:
                            result = await handler(step_def.get("config", {}), context, step)
                            branch_results.append({"step_type": step_type, "result": result, "status": "completed"})
                        except Exception as exc:
                            branch_results.append({"step_type": step_type, "error": str(exc), "status": "failed"})
                            branch_status = "failed"
                    else:
                        branch_results.append({"step_type": step_type, "error": "no handler", "status": "skipped"})
                return {"branch_index": branch_idx, "results": branch_results, "status": branch_status}

        tasks = [_run_branch(branch, idx) for idx, branch in enumerate(branches)]
        branch_results = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[dict[str, Any]] = []
        for idx, res in enumerate(branch_results):
            if isinstance(res, Exception):
                results.append({"branch_index": idx, "error": str(res), "status": "failed"})
            else:
                results.append(res)

        return {"branches_count": len(branches), "results": results}

    # ── Action step handlers ───────────────────────────────────────────────

    async def _handle_send_email(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        to = _resolve_config(config.get("to", ""), context)
        subject = _resolve_config(config.get("subject", ""), context)
        body = _resolve_config(config.get("body", ""), context)
        logger.info("Sending email to=%s subject=%s", to, subject)
        if not to:
            raise ValueError("send_email: 'to' address is required")
        return {"to": to, "subject": subject, "body_preview": body[:100] if body else "", "sent": True}

    async def _handle_update_crm(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        entity = config.get("entity", "")
        entity_id = _resolve_config(str(config.get("entity_id", "")), context)
        fields = config.get("fields", {})
        logger.info("Updating CRM %s %s with %s", entity, entity_id, fields)
        if not entity_id:
            raise ValueError("update_crm: 'entity_id' is required")
        return {"entity": entity, "entity_id": entity_id, "fields": fields, "updated": True}

    async def _handle_create_task(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        title = _resolve_config(config.get("title", ""), context)
        assignee = _resolve_config(config.get("assignee", ""), context)
        description = _resolve_config(config.get("description", ""), context)
        logger.info("Creating task title=%s assignee=%s", title, assignee)
        if not title:
            raise ValueError("create_task: 'title' is required")
        return {"title": title, "assignee": assignee, "description": description, "created": True}

    async def _handle_webhook(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        url = _resolve_config(config.get("url", ""), context)
        method = config.get("method", "POST")
        logger.info("Calling webhook url=%s method=%s", url, method)
        if not url:
            raise ValueError("webhook: 'url' is required")
        return {"url": url, "method": method, "status_code": 200, "called": True}

    async def _handle_nba_recommend(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        action = config.get("action", "")
        reason = _resolve_config(config.get("reason", ""), context)
        logger.info("NBA recommend action=%s reason=%s", action, reason)
        return {"action": action, "reason": reason, "recommended": True}

    async def _handle_set_variable(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        """Set a variable in the context."""
        var_name = config.get("name", "")
        var_value = _resolve_config(config.get("value", ""), context)
        if not var_name:
            raise ValueError("set_variable: 'name' is required")
        context[var_name] = var_value
        return {"name": var_name, "value": var_value, "set": True}

    async def _handle_log_message(
        self,
        config: dict[str, Any],
        context: dict[str, Any],
        step: WorkflowStep | None = None,
    ) -> dict[str, Any]:
        """Log a message during workflow execution."""
        level = config.get("level", "info")
        message = _resolve_config(config.get("message", ""), context)
        log_fn = getattr(logger, level.lower(), logger.info)
        log_fn("Workflow log: %s", message)
        return {"level": level, "message": message, "logged": True}


    async def _emit_execution_event(self, workflow: Workflow, execution: WorkflowExecution) -> None:
        if not self._event_bus or WorkflowCompleted is None:
            return
        try:
            if execution.status == "completed":
                event = WorkflowCompleted(
                    aggregate_id=workflow.id,
                    tenant_id=workflow.tenant_id,
                    data={
                        "execution_id": execution.id,
                        "workflow_name": workflow.name,
                        "trigger_event": execution.trigger_event,
                        "step_count": len(execution.step_results),
                    },
                )
                await self._event_bus.publish(event)
            elif execution.status in ("failed", "timed_out"):
                event = WorkflowFailed(
                    aggregate_id=workflow.id,
                    tenant_id=workflow.tenant_id,
                    data={
                        "execution_id": execution.id,
                        "workflow_name": workflow.name,
                        "error": execution.error or "",
                        "trigger_event": execution.trigger_event,
                    },
                )
                await self._event_bus.publish(event)
        except Exception:
            logger.exception("Failed to emit workflow execution event")


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
