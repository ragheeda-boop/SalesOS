"""Pre-built workflow templates and template registry."""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from domains.workflow.models import Workflow, WorkflowStep, WorkflowTemplate


def _step_id() -> str:
    return uuid.uuid4().hex[:12]


def _template_id() -> str:
    return f"tmpl_{uuid.uuid4().hex[:8]}"


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


def _make_template(
    name: str,
    description: str,
    category: str,
    steps: list[dict[str, Any]],
    variables: list[dict[str, Any]] | None = None,
    trigger_type: str = "manual",
    tags: list[str] | None = None,
) -> WorkflowTemplate:
    return WorkflowTemplate(
        id=_template_id(),
        name=name,
        description=description,
        category=category,
        steps=steps,
        variables=variables or [],
        trigger_type=trigger_type,
        tags=tags or [],
    )


# ── Legacy workflow objects (backward compatible) ────────────────────────

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


# ── NEW: Phase 13 templates ─────────────────────────────────────────────

LEAD_ASSIGNMENT = _make_wf(
    name="Lead Assignment",
    description="Round-robin or territory-based lead assignment with CRM update",
    trigger_type="event",
    steps=[
        {
            "type": "set_variable",
            "config": {
                "name": "assigned_rep",
                "value": "{{context.round_robin_rep}}",
            },
        },
        {
            "type": "update_crm",
            "config": {
                "entity": "lead",
                "entity_id": "{{context.lead_id}}",
                "fields": {"owner": "{{context.assigned_rep}}", "assigned_at": "{{context.timestamp}}"},
            },
        },
        {
            "type": "send_email",
            "config": {
                "to": "{{context.assigned_rep_email}}",
                "subject": "New lead assigned: {{context.lead_name}}",
                "body": "You have been assigned a new lead: {{context.lead_name}} from {{context.company}}. Please follow up within 24 hours.",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Initial outreach to {{context.lead_name}}",
                "assignee": "{{context.assigned_rep}}",
                "description": "Contact new lead {{context.lead_name}} from {{context.company}} within 24 hours",
            },
        },
    ],
)

DEAL_ESCALATION = _make_wf(
    name="Deal Escalation",
    description="When deal value exceeds threshold, notify manager and create review task",
    trigger_type="event",
    steps=[
        {
            "type": "if_else",
            "config": {
                "condition": "context.amount > 50000",
                "then_steps": [
                    {
                        "step_type": "send_email",
                        "config": {
                            "to": "{{context.manager_email}}",
                            "subject": "High-value deal requires review: {{context.deal_name}}",
                            "body": "Deal '{{context.deal_name}}' worth {{context.amount}} requires your review and approval.",
                        },
                    },
                    {
                        "step_type": "create_task",
                        "config": {
                            "title": "Review high-value deal: {{context.deal_name}}",
                            "assignee": "{{context.manager}}",
                            "description": "Review and approve deal {{context.deal_name}} ({{context.amount}})",
                        },
                    },
                ],
                "else_steps": [
                    {
                        "step_type": "update_crm",
                        "config": {
                            "entity": "opportunity",
                            "entity_id": "{{context.deal_id}}",
                            "fields": {"escalated": False},
                        },
                    },
                ],
            },
        },
    ],
)

RENEWAL_REMINDERS = _make_wf(
    name="Renewal Reminders",
    description="Send renewal reminders at 30, 15, and 7 days before renewal date",
    trigger_type="event",
    steps=[
        {
            "type": "for_each",
            "config": {
                "collection_key": "renewal_dates",
                "item_var": "renewal",
                "steps": [
                    {
                        "step_type": "send_email",
                        "config": {
                            "to": "{{context.account_owner_email}}",
                            "subject": "Renewal reminder: {{context.renewal.company}}",
                            "body": "Contract for {{context.renewal.company}} renews on {{context.renewal.date}}. Amount: {{context.renewal.amount}}.",
                        },
                    },
                    {
                        "step_type": "create_task",
                        "config": {
                            "title": "Prepare renewal for {{context.renewal.company}}",
                            "assignee": "{{context.account_owner}}",
                            "description": "Prepare renewal proposal for {{context.renewal.company}}, expires {{context.renewal.date}}",
                        },
                    },
                ],
            },
        },
    ],
)

EMPLOYEE_ONBOARDING = _make_wf(
    name="Employee Onboarding",
    description="Automated new hire task sequence — equipment, accounts, training",
    trigger_type="event",
    steps=[
        {
            "type": "create_task",
            "config": {
                "title": "Provision equipment for {{context.employee_name}}",
                "assignee": "{{context.it_owner}}",
                "description": "Set up laptop, peripherals, and badge for new hire {{context.employee_name}} starting {{context.start_date}}",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Create accounts for {{context.employee_name}}",
                "assignee": "{{context.it_owner}}",
                "description": "Create email, Slack, and application accounts for {{context.employee_name}} ({{context.department}})",
            },
        },
        {
            "type": "send_email",
            "config": {
                "to": "{{context.employee_email}}",
                "subject": "Welcome to the team, {{context.employee_name}}!",
                "body": "We're excited to have you join the {{context.department}} team. Your start date is {{context.start_date}}. Please review the onboarding checklist.",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Schedule onboarding training for {{context.employee_name}}",
                "assignee": "{{context.hr_owner}}",
                "description": "Schedule orientation, compliance training, and team introductions for {{context.employee_name}}",
            },
        },
    ],
)

FOLLOWUP_AUTOMATION = _make_wf(
    name="Follow-up Automation",
    description="Send reminder N days after meeting, with escalation if no response",
    trigger_type="event",
    steps=[
        {
            "type": "send_email",
            "config": {
                "to": "{{context.contact_email}}",
                "subject": "Follow-up: {{context.meeting_topic}}",
                "body": "Hi {{context.contact_name}}, following up on our meeting about {{context.meeting_topic}}. Please let me know if you have any questions.",
            },
        },
        {
            "type": "create_task",
            "config": {
                "title": "Track response from {{context.contact_name}}",
                "assignee": "{{context.owner}}",
                "description": "Monitor for response to follow-up email about {{context.meeting_topic}}. Escalate if no reply in 48h.",
            },
        },
        {
            "type": "if_else",
            "config": {
                "condition": "context.deal_amount > 25000",
                "then_steps": [
                    {
                        "step_type": "webhook",
                        "config": {
                            "url": "{{context.escalation_webhook}}",
                            "method": "POST",
                        },
                    },
                ],
                "else_steps": [],
            },
        },
    ],
)


# ── Template Registry ───────────────────────────────────────────────────

WORKFLOW_TEMPLATES: dict[str, Workflow] = {
    "lead_followup": LEAD_FOLLOWUP,
    "deal_review": DEAL_REVIEW,
    "meeting_prep": MEETING_PREP,
    "lost_deal_analysis": LOST_DEAL_ANALYSIS,
    "lead_assignment": LEAD_ASSIGNMENT,
    "deal_escalation": DEAL_ESCALATION,
    "renewal_reminders": RENEWAL_REMINDERS,
    "employee_onboarding": EMPLOYEE_ONBOARDING,
    "followup_automation": FOLLOWUP_AUTOMATION,
}

WORKFLOW_TEMPLATE_REGISTRY: dict[str, WorkflowTemplate] = {
    "lead_followup": _make_template(
        name="Lead Follow-up",
        description="On NBA recommendation → Send email + Create task",
        category="lead",
        trigger_type="event",
        tags=["lead", "follow-up", "email"],
        variables=[
            {"name": "lead_email", "type": "string", "required": True, "description": "Lead email address"},
            {"name": "lead_name", "type": "string", "required": True, "description": "Lead full name"},
            {"name": "product_interest", "type": "string", "required": False, "description": "Product of interest"},
            {"name": "owner", "type": "string", "required": True, "description": "Assigned owner"},
        ],
        steps=[
            {"step_type": "send_email", "config": {"to": "{{context.lead_email}}", "subject": "Following up on {{context.product_interest}}", "body": "Hi, I noticed you were interested in {{context.product_interest}}."}},
            {"step_type": "create_task", "config": {"title": "Follow up with {{context.lead_name}}", "assignee": "{{context.owner}}", "description": "Send follow-up email and track response"}},
        ],
    ),
    "deal_review": _make_template(
        name="Deal Review",
        description="On stage change → Notify team + Update CRM",
        category="deal",
        trigger_type="event",
        tags=["deal", "stage", "crm"],
        variables=[
            {"name": "deal_name", "type": "string", "required": True},
            {"name": "deal_id", "type": "string", "required": True},
            {"name": "stage", "type": "string", "required": True},
            {"name": "team_email", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "send_email", "config": {"to": "{{context.team_email}}", "subject": "Deal moved to {{context.stage}}", "body": "Please review the deal stage change."}},
            {"step_type": "update_crm", "config": {"entity": "opportunity", "entity_id": "{{context.deal_id}}", "fields": {"stage": "{{context.stage}}"}}},
        ],
    ),
    "meeting_prep": _make_template(
        name="Meeting Prep",
        description="On meeting scheduled → Generate brief + Create task",
        category="follow_up",
        trigger_type="event",
        tags=["meeting", "brief", "preparation"],
        variables=[
            {"name": "contact_name", "type": "string", "required": True},
            {"name": "owner", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "nba_recommend", "config": {"action": "generate_brief", "reason": "Meeting with {{context.contact_name}}"}},
            {"step_type": "create_task", "config": {"title": "Prepare for {{context.contact_name}}", "assignee": "{{context.owner}}", "description": "Review brief and talking points"}},
        ],
    ),
    "lost_deal_analysis": _make_template(
        name="Lost Deal Analysis",
        description="On deal lost → Create analysis task + Notify manager",
        category="deal",
        trigger_type="event",
        tags=["deal", "lost", "analysis"],
        variables=[
            {"name": "deal_name", "type": "string", "required": True},
            {"name": "amount", "type": "number", "required": True},
            {"name": "competitor", "type": "string", "required": False},
            {"name": "manager_email", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "create_task", "config": {"title": "Analyze lost deal: {{context.deal_name}}", "assignee": "{{context.owner}}", "description": "Win/loss analysis"}},
            {"step_type": "send_email", "config": {"to": "{{context.manager_email}}", "subject": "Deal lost: {{context.deal_name}}", "body": "Deal was lost to {{context.competitor}}."}, "condition": "context.amount > 10000"},
        ],
    ),
    "lead_assignment": _make_template(
        name="Lead Assignment",
        description="Round-robin or territory-based lead assignment with CRM update",
        category="lead",
        trigger_type="event",
        tags=["lead", "assignment", "round-robin"],
        variables=[
            {"name": "lead_id", "type": "string", "required": True},
            {"name": "lead_name", "type": "string", "required": True},
            {"name": "company", "type": "string", "required": False},
            {"name": "round_robin_rep", "type": "string", "required": True, "description": "Next rep in rotation"},
            {"name": "assigned_rep_email", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "set_variable", "config": {"name": "assigned_rep", "value": "{{context.round_robin_rep}}"}},
            {"step_type": "update_crm", "config": {"entity": "lead", "entity_id": "{{context.lead_id}}", "fields": {"owner": "{{context.assigned_rep}}"}}},
            {"step_type": "send_email", "config": {"to": "{{context.assigned_rep_email}}", "subject": "New lead assigned: {{context.lead_name}}", "body": "Follow up within 24 hours."}},
            {"step_type": "create_task", "config": {"title": "Initial outreach to {{context.lead_name}}", "assignee": "{{context.assigned_rep}}", "description": "Contact new lead within 24h"}},
        ],
    ),
    "deal_escalation": _make_template(
        name="Deal Escalation",
        description="When deal value exceeds threshold, notify manager and create review task",
        category="deal",
        trigger_type="event",
        tags=["deal", "escalation", "threshold"],
        variables=[
            {"name": "deal_name", "type": "string", "required": True},
            {"name": "amount", "type": "number", "required": True},
            {"name": "manager_email", "type": "string", "required": True},
            {"name": "manager", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "if_else", "config": {
                "condition": "context.amount > 50000",
                "then_steps": [
                    {"step_type": "send_email", "config": {"to": "{{context.manager_email}}", "subject": "High-value deal review", "body": "Deal {{context.deal_name}} worth {{context.amount}} requires review."}},
                    {"step_type": "create_task", "config": {"title": "Review high-value deal", "assignee": "{{context.manager}}", "description": "Review and approve"}},
                ],
                "else_steps": [],
            }},
        ],
    ),
    "renewal_reminders": _make_template(
        name="Renewal Reminders",
        description="Send renewal reminders at 30, 15, and 7 days before renewal date",
        category="renewal",
        trigger_type="event",
        tags=["renewal", "reminder", "contract"],
        variables=[
            {"name": "renewal_dates", "type": "array", "required": True, "description": "List of renewal objects"},
            {"name": "account_owner", "type": "string", "required": True},
            {"name": "account_owner_email", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "for_each", "config": {
                "collection_key": "renewal_dates",
                "item_var": "renewal",
                "steps": [
                    {"step_type": "send_email", "config": {"to": "{{context.account_owner_email}}", "subject": "Renewal reminder: {{context.renewal.company}}", "body": "Contract renews on {{context.renewal.date}}."}},
                    {"step_type": "create_task", "config": {"title": "Prepare renewal for {{context.renewal.company}}", "assignee": "{{context.account_owner}}", "description": "Prepare renewal proposal"}},
                ],
            }},
        ],
    ),
    "employee_onboarding": _make_template(
        name="Employee Onboarding",
        description="Automated new hire task sequence — equipment, accounts, training",
        category="onboarding",
        trigger_type="event",
        tags=["onboarding", "new-hire", "hr"],
        variables=[
            {"name": "employee_name", "type": "string", "required": True},
            {"name": "employee_email", "type": "string", "required": True},
            {"name": "department", "type": "string", "required": True},
            {"name": "start_date", "type": "string", "required": True},
            {"name": "it_owner", "type": "string", "required": True},
            {"name": "hr_owner", "type": "string", "required": True},
        ],
        steps=[
            {"step_type": "create_task", "config": {"title": "Provision equipment", "assignee": "{{context.it_owner}}", "description": "Set up laptop, peripherals, badge"}},
            {"step_type": "create_task", "config": {"title": "Create accounts", "assignee": "{{context.it_owner}}", "description": "Email, Slack, app accounts"}},
            {"step_type": "send_email", "config": {"to": "{{context.employee_email}}", "subject": "Welcome to the team!", "body": "We're excited to have you join {{context.department}}."}},
            {"step_type": "create_task", "config": {"title": "Schedule onboarding training", "assignee": "{{context.hr_owner}}", "description": "Orientation, compliance, team introductions"}},
        ],
    ),
    "followup_automation": _make_template(
        name="Follow-up Automation",
        description="Send reminder N days after meeting, with escalation if no response",
        category="follow_up",
        trigger_type="event",
        tags=["follow-up", "meeting", "escalation"],
        variables=[
            {"name": "contact_name", "type": "string", "required": True},
            {"name": "contact_email", "type": "string", "required": True},
            {"name": "meeting_topic", "type": "string", "required": True},
            {"name": "owner", "type": "string", "required": True},
            {"name": "deal_amount", "type": "number", "required": False},
            {"name": "escalation_webhook", "type": "string", "required": False},
        ],
        steps=[
            {"step_type": "send_email", "config": {"to": "{{context.contact_email}}", "subject": "Follow-up: {{context.meeting_topic}}", "body": "Following up on our meeting about {{context.meeting_topic}}."}},
            {"step_type": "create_task", "config": {"title": "Track response from {{context.contact_name}}", "assignee": "{{context.owner}}", "description": "Monitor for response, escalate if no reply in 48h"}},
            {"step_type": "if_else", "config": {
                "condition": "context.deal_amount > 25000",
                "then_steps": [{"step_type": "webhook", "config": {"url": "{{context.escalation_webhook}}", "method": "POST"}}],
                "else_steps": [],
            }},
        ],
    ),
}
