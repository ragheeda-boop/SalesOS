"""Workflow Event Subscriber — subscribes to DomainEvent bus and executes event-triggered workflows.

Listens for domain events (opportunity.stage_changed, meeting.completed, etc.),
matches event type to active workflow templates with trigger_type="event",
and calls WorkflowEngine.execute() with the event data.
"""

from __future__ import annotations

import logging
from typing import Any

from domains.workflow.models import Workflow
from domains.workflow.service import WorkflowService
from domains.workflow.engine import WorkflowEngine

logger = logging.getLogger(__name__)

# Maps domain event types to workflow matching strategies.
# Workflows with trigger_type="event" are matched when their
# template name/trigger config aligns with the event type.
EVENT_TO_WORKFLOW_TRIGGER: dict[str, list[str]] = {
    "opportunity.created": ["lead_followup"],
    "opportunity.stage_changed": ["deal_review"],
    "opportunity.won": [],
    "opportunity.lost": ["lost_deal_analysis"],
    "meeting.scheduled": ["meeting_prep"],
    "activity.logged": [],
}


class WorkflowEventSubscriber:
    """Subscribes to the event bus and dispatches events to matching workflows."""

    def __init__(
        self,
        workflow_service: WorkflowService,
        event_bus: Any,
        engine: WorkflowEngine | None = None,
    ):
        self._workflow_service = workflow_service
        self._event_bus = event_bus
        self._engine = engine or getattr(workflow_service, "_engine", None)

    async def start(self) -> None:
        """Subscribe to all relevant event types on the event bus."""
        event_types = list(EVENT_TO_WORKFLOW_TRIGGER.keys())
        self._event_bus.subscribe("*", self._handle_event)
        logger.info(
            "WorkflowEventSubscriber subscribed to %d event types",
            len(event_types),
        )

    async def _handle_event(self, event: Any) -> None:
        """Handle an incoming domain event — match and execute workflows."""
        event_type = getattr(event, "event_type", "")
        tenant_id = getattr(event, "tenant_id", "")
        data = getattr(event, "data", {})
        if not event_type or not tenant_id:
            return

        logger.debug("Workflow subscriber received event: %s", event_type)

        workflows = await self._workflow_service.list(tenant_id)
        matching = self._match_workflows(event_type, workflows)

        if not matching:
            return

        context = {
            "trigger": event_type,
            "event_id": getattr(event, "event_id", ""),
            "tenant_id": tenant_id,
            **data,
        }

        for wf in matching:
            try:
                execution = await self._workflow_service.execute(
                    wf.id, tenant_id, context=context,
                )
                logger.info(
                    "Workflow '%s' (%s) executed for event %s: status=%s",
                    wf.name, wf.id, event_type, execution.status,
                )
            except Exception:
                logger.exception(
                    "Workflow '%s' (%s) failed for event %s",
                    wf.name, wf.id, event_type,
                )

    def _match_workflows(
        self, event_type: str, workflows: list[Workflow],
    ) -> list[Workflow]:
        """Match an event type against active, event-triggered workflows."""
        matched: list[Workflow] = []
        for wf in workflows:
            if wf.status != "active":
                continue
            if wf.trigger_type != "event":
                continue
            # Match by event type stored in workflow metadata or config
            trigger_config = wf.description or ""
            if event_type in trigger_config or event_type in EVENT_TO_WORKFLOW_TRIGGER:
                matched.append(wf)
            # Also match by template name convention
            for tmpl_name in EVENT_TO_WORKFLOW_TRIGGER.get(event_type, []):
                if tmpl_name in wf.name.lower().replace(" ", "_"):
                    if wf not in matched:
                        matched.append(wf)
        return matched