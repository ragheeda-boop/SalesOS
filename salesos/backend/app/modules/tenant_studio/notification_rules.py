"""STORY-10-08 — CAP-093 Notification Rules Studio models.

Tenant-defined event → channel routing. Compiles to rules_engine send_notification.
Not Production GO. DEC-085 untouched. No Alembic / FORCE RLS.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Channel = Literal["in_app", "email"]
RecipientKind = Literal["role", "user", "owner"]

VALID_EVENT_TYPES: frozenset[str] = frozenset(
    {
        "opportunity.stage_changed",
        "lead.assigned",
        "task.overdue",
        "sync.failed",
        "score.threshold",
    }
)
VALID_CHANNELS: frozenset[str] = frozenset({"in_app", "email"})
VALID_RECIPIENT_KINDS: frozenset[str] = frozenset({"role", "user", "owner"})
VALID_OPERATORS: frozenset[str] = frozenset(
    {"equals", "not_equals", "greater_than", "less_than", "contains", "in", "not_in"}
)

# Map Studio events → rules_engine DomainType.
EVENT_DOMAIN: dict[str, str] = {
    "opportunity.stage_changed": "opportunity",
    "lead.assigned": "company",
    "task.overdue": "workflow",
    "sync.failed": "workflow",
    "score.threshold": "scoring",
}


class NotificationRuleError(ValueError):
    """Invalid notification rule definition."""


@dataclass
class RouteCondition:
    field: str
    operator: str
    value: Any

    def as_dict(self) -> dict[str, Any]:
        return {
            "field": self.field,
            "operator": self.operator,
            "value": self.value,
        }


@dataclass
class RouteRecipient:
    kind: RecipientKind
    value: str  # role name, user id, or "owner"

    def as_dict(self) -> dict[str, Any]:
        return {"kind": self.kind, "value": self.value}


@dataclass
class NotificationRule:
    id: str
    tenant_id: str
    name: str
    event_type: str
    channels: list[str] = field(default_factory=list)
    recipients: list[RouteRecipient] = field(default_factory=list)
    conditions: list[RouteCondition] = field(default_factory=list)
    message_template: str = ""
    priority: int = 100
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "tenant_id": self.tenant_id,
            "name": self.name,
            "event_type": self.event_type,
            "channels": list(self.channels),
            "recipients": [r.as_dict() for r in self.recipients],
            "conditions": [c.as_dict() for c in self.conditions],
            "message_template": self.message_template,
            "priority": self.priority,
            "active": self.active,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


def _parse_conditions(raw: list[dict[str, Any]] | list[RouteCondition]) -> list[RouteCondition]:
    out: list[RouteCondition] = []
    for item in raw or []:
        if isinstance(item, RouteCondition):
            cond = item
        elif isinstance(item, dict):
            field_name = str(item.get("field") or "").strip()
            op = str(item.get("operator") or "").strip()
            if not field_name:
                raise NotificationRuleError("condition.field required")
            if op not in VALID_OPERATORS:
                raise NotificationRuleError(f"unsupported operator: {op}")
            cond = RouteCondition(field=field_name, operator=op, value=item.get("value"))
        else:
            raise NotificationRuleError("condition must be a mapping")
        out.append(cond)
    return out


def _parse_recipients(
    raw: list[dict[str, Any]] | list[RouteRecipient],
) -> list[RouteRecipient]:
    out: list[RouteRecipient] = []
    for item in raw or []:
        if isinstance(item, RouteRecipient):
            rec = item
        elif isinstance(item, dict):
            kind = str(item.get("kind") or "").strip().lower()
            value = str(item.get("value") or "").strip()
            if kind not in VALID_RECIPIENT_KINDS:
                raise NotificationRuleError(f"unsupported recipient kind: {kind}")
            if not value:
                raise NotificationRuleError("recipient.value required")
            rec = RouteRecipient(kind=kind, value=value)  # type: ignore[arg-type]
        else:
            raise NotificationRuleError("recipient must be a mapping")
        out.append(rec)
    return out


def _parse_channels(raw: list[str]) -> list[str]:
    channels: list[str] = []
    for ch in raw or []:
        c = str(ch).strip().lower()
        if c not in VALID_CHANNELS:
            raise NotificationRuleError(f"unsupported channel: {c}")
        if c not in channels:
            channels.append(c)
    if not channels:
        raise NotificationRuleError("channels required (non-empty)")
    return channels


def build_notification_rule(
    *,
    tenant_id: str,
    name: str,
    event_type: str,
    channels: list[str],
    recipients: list[dict[str, Any]] | list[RouteRecipient],
    conditions: list[dict[str, Any]] | list[RouteCondition] | None = None,
    message_template: str = "",
    priority: int = 100,
    active: bool = True,
    rule_id: str = "",
    schema_version: int = 1,
) -> NotificationRule:
    tid = (tenant_id or "").strip()
    if not tid:
        raise NotificationRuleError("tenant_id required")
    nm = (name or "").strip()
    if not nm:
        raise NotificationRuleError("name required")
    et = (event_type or "").strip()
    if et not in VALID_EVENT_TYPES:
        raise NotificationRuleError(f"event_type must be one of {sorted(VALID_EVENT_TYPES)}")
    recs = _parse_recipients(list(recipients))
    if not recs:
        raise NotificationRuleError("recipients required (non-empty)")
    return NotificationRule(
        id=rule_id,
        tenant_id=tid,
        name=nm,
        event_type=et,
        channels=_parse_channels(list(channels)),
        recipients=recs,
        conditions=_parse_conditions(list(conditions or [])),
        message_template=(message_template or "").strip(),
        priority=int(priority),
        active=bool(active),
        schema_version=max(int(schema_version), 1),
    )
