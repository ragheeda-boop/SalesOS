"""STORY-10-08 — Compile Studio notification rules → rules_engine + route events.

No second notification interpreter — uses RulesEngine send_notification actions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.rules_engine.engine import evaluate_rule
from app.modules.rules_engine.models import (
    Action,
    ActionType,
    Condition,
    ConditionGroup,
    ConditionGroupType,
    ConditionOperator,
    Rule,
    RuleEvaluationContext,
)
from app.modules.tenant_studio.notification_rules import (
    EVENT_DOMAIN,
    NotificationRule,
    NotificationRuleError,
)

_OP_MAP: dict[str, ConditionOperator] = {
    "equals": ConditionOperator.equals,
    "not_equals": ConditionOperator.not_equals,
    "greater_than": ConditionOperator.greater_than,
    "less_than": ConditionOperator.less_than,
    "contains": ConditionOperator.contains,
    "in": ConditionOperator.in_,
    "not_in": ConditionOperator.not_in,
}


def compile_notification_rule(rule: NotificationRule) -> Rule:
    """Translate Studio rule into rules_engine Rule (send_notification actions)."""
    if not rule.channels:
        raise NotificationRuleError("channels required")
    if not rule.recipients:
        raise NotificationRuleError("recipients required")

    conditions: list[Condition | ConditionGroup] = [
        Condition(
            field="event_type",
            operator=ConditionOperator.equals,
            value=rule.event_type,
        )
    ]
    for c in rule.conditions:
        op = _OP_MAP.get(c.operator)
        if op is None:
            raise NotificationRuleError(f"unsupported operator: {c.operator}")
        conditions.append(Condition(field=c.field, operator=op, value=c.value))

    domain = EVENT_DOMAIN.get(rule.event_type, "workflow")
    actions = [
        Action(
            type=ActionType.send_notification,
            params={
                "channel": ch,
                "message": rule.message_template,
                "recipients": [r.as_dict() for r in rule.recipients],
                "event_type": rule.event_type,
                "studio_rule_id": rule.id,
            },
        )
        for ch in rule.channels
    ]
    return Rule(
        id=rule.id or rule.name,
        name=rule.name,
        description=f"Studio notification rule for {rule.event_type}",
        enabled=rule.active,
        domain=domain,  # type: ignore[arg-type]
        conditions=ConditionGroup(
            type=ConditionGroupType.and_,
            conditions=conditions,
        ),
        actions=actions,
        priority=rule.priority,
    )


def _render_message(template: str, payload: dict[str, Any]) -> str:
    msg = template or ""
    for key, val in payload.items():
        msg = msg.replace("{" + str(key) + "}", str(val))
    return msg


@dataclass
class NotificationRoute:
    rule_id: str
    rule_name: str
    channels: list[str]
    recipients: list[dict[str, Any]]
    message: str
    actions: list[dict[str, Any]] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "rule_name": self.rule_name,
            "channels": list(self.channels),
            "recipients": list(self.recipients),
            "message": self.message,
            "actions": list(self.actions),
        }


@dataclass
class NotificationRoutingResult:
    event_type: str
    matched: bool
    routes: list[NotificationRoute] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "event_type": self.event_type,
            "matched": self.matched,
            "routes": [r.as_dict() for r in self.routes],
            "route_count": len(self.routes),
        }


def route_notification_event(
    rules: list[NotificationRule],
    *,
    event_type: str,
    payload: dict[str, Any] | None = None,
    entity_id: str = "event",
) -> NotificationRoutingResult:
    """Evaluate active Studio rules via rules_engine (send_notification)."""
    et = (event_type or "").strip()
    data = dict(payload or {})
    data["event_type"] = et
    domain = EVENT_DOMAIN.get(et, "workflow")
    context = RuleEvaluationContext(
        entity_id=entity_id,
        entity_type=domain,  # type: ignore[arg-type]
        data=data,
    )

    routes: list[NotificationRoute] = []
    ordered = sorted(
        [r for r in rules if r.active and r.event_type == et],
        key=lambda r: r.priority,
    )
    for studio_rule in ordered:
        engine_rule = compile_notification_rule(studio_rule)
        result = evaluate_rule(engine_rule, context)
        if not result.matched or not result.actions_executed:
            continue
        message = _render_message(studio_rule.message_template, data)
        # Stamp rendered message onto executed action payloads for callers.
        actions = []
        for act in result.actions_executed:
            row = dict(act)
            row["message"] = message
            actions.append(row)
        routes.append(
            NotificationRoute(
                rule_id=studio_rule.id,
                rule_name=studio_rule.name,
                channels=list(studio_rule.channels),
                recipients=[r.as_dict() for r in studio_rule.recipients],
                message=message,
                actions=actions,
            )
        )
    return NotificationRoutingResult(event_type=et, matched=len(routes) > 0, routes=routes)
