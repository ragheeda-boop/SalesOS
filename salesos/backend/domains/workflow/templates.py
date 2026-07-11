"""Pre-built workflow templates."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import Workflow, WorkflowStep


def _step_id() -> str:
    return uuid.uuid4().hex[:12]


def _make_wf(
    name: str,
    description: str,
    trigger_type: str,
    steps: list[dict[str, Any]],
) -> Workflow:
    wf = Workflow(
        id=uuid.uuid4().hex[:12],
        tenant_id="template",
        name=name,
        description=description,
        trigger_type=trigger_type,
        status="draft",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    wf.steps = [
        WorkflowStep(
            id=_step_id(),
            workflow_id=wf.id,
            step_type=s["type"],
            config=s.get("config", {}),
            order=i,
            condition=s.get("condition"),
        )
        for i, s in enumerate(steps)
    ]
    return wf


LEAD_FOLLOWUP = _make_wf(
    name="Lead Follow-up",
    description="On NBA recommendation → Send email + Create task",
    trigger_type="event",
    steps=[
        {
            "type": "send_email",
            "config": {
                "to": "{{context.lead_email}}",
                "subject": "Following up on {{context.product_interest}}",
                "body": "Hi, I noticed you were interested in {{context.product_interest}}. Let me know if you have any questions!",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Follow up with {{context.lead_name}}",
                "assignee": "{{context.owner}}",
                "description": "Send follow-up email and track response for lead {{context.lead_name}}",
            },
        },
    ],
)

DEAL_REVIEW = _make_wf(
    name="Deal Review",
    description="On stage change → Notify team + Update CRM",
    trigger_type="event",
    steps=[
        {
            "type": "send_email",
            "config": {
                "to": "{{context.team_email}}",
                "subject": "Deal {{context.deal_name}} moved to {{context.stage}}",
                "body": "The deal {{context.deal_name}} has moved to stage {{context.stage}}. Please review.",
            },
        },
        {
            "type": "update_crm",
            "config": {
                "entity": "opportunity",
                "entity_id": "{{context.deal_id}}",
                "fields": {"last_reviewed": "{{context.timestamp}}", "stage": "{{context.stage}}"},
            },
        },
    ],
)

MEETING_PREP = _make_wf(
    name="Meeting Prep",
    description="On meeting scheduled → Generate brief + Create task",
    trigger_type="event",
    steps=[
        {
            "type": "nba_recommend",
            "config": {
                "action": "generate_brief",
                "reason": "Meeting scheduled with {{context.contact_name}} — generating prep brief",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Prepare for meeting with {{context.contact_name}}",
                "assignee": "{{context.owner}}",
                "description": "Review generated brief and prepare talking points for {{context.contact_name}}",
            },
        },
    ],
)

LOST_DEAL_ANALYSIS = _make_wf(
    name="Lost Deal Analysis",
    description="On deal lost → Create analysis task + Notify manager",
    trigger_type="event",
    steps=[
        {
            "type": "create_task",
            "config": {
                "title": "Analyze lost deal: {{context.deal_name}}",
                "assignee": "{{context.owner}}",
                "description": "Perform win/loss analysis for deal {{context.deal_name}} lost to {{context.competitor}}",
            },
        },
        {
            "type": "send_email",
            "config": {
                "to": "{{context.manager_email}}",
                "subject": "Deal lost: {{context.deal_name}}",
                "body": "Deal {{context.deal_name}} ({{context.amount}}) was lost to {{context.competitor}}. Analysis task created.",
            },
            "condition": "context.amount > 10000",
        },
    ],
)

WORKFLOW_TEMPLATES: dict[str, Workflow] = {
    "lead_followup": LEAD_FOLLOWUP,
    "deal_review": DEAL_REVIEW,
    "meeting_prep": MEETING_PREP,
    "lost_deal_analysis": LOST_DEAL_ANALYSIS,
}
