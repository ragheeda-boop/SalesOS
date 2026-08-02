"""STORY-10-08 — In-memory Notification Rules store (no Alembic / FORCE RLS)."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.rules_engine.models import Rule
from app.modules.tenant_studio.notification_rules import (
    NotificationRule,
    NotificationRuleError,
    build_notification_rule,
)
from app.modules.tenant_studio.notification_rules_engine import (
    NotificationRoutingResult,
    compile_notification_rule,
    route_notification_event,
)


@dataclass
class MemNotificationRulesStore:
    """Tenant-scoped notification routing rules for CAP-093 Studio."""

    _by_id: dict[str, NotificationRule] = field(default_factory=dict)

    def upsert(
        self,
        *,
        tenant_id: str,
        name: str,
        event_type: str,
        channels: list[str],
        recipients: list[dict[str, Any]],
        conditions: list[dict[str, Any]] | None = None,
        message_template: str = "",
        priority: int = 100,
        active: bool = True,
        rule_id: str | None = None,
    ) -> NotificationRule:
        tid = str(tenant_id)
        now = datetime.now(UTC).isoformat()
        rid = (rule_id or "").strip()
        existing = self._by_id.get(rid) if rid else None
        if existing and existing.tenant_id != tid:
            raise PermissionError("cross-tenant notification rule write blocked")
        schema_version = 1
        created_at = now
        if existing:
            schema_version = max(existing.schema_version + 1, 1)
            created_at = existing.created_at or now
        else:
            rid = rid or uuid.uuid4().hex[:12]

        rule = build_notification_rule(
            tenant_id=tid,
            name=name,
            event_type=event_type,
            channels=channels,
            recipients=recipients,
            conditions=conditions,
            message_template=message_template,
            priority=priority,
            active=active,
            rule_id=rid,
            schema_version=schema_version,
        )
        # Validate compile path early (fail closed on bad rule).
        compile_notification_rule(rule)
        rule.created_at = created_at
        rule.updated_at = now
        self._by_id[rule.id] = rule
        return rule

    def get(self, rule_id: str, *, tenant_id: str) -> NotificationRule | None:
        row = self._by_id.get(str(rule_id))
        if row is None or row.tenant_id != str(tenant_id):
            return None
        return row

    def list_for_tenant(self, *, tenant_id: str) -> list[NotificationRule]:
        tid = str(tenant_id)
        return sorted(
            [r for r in self._by_id.values() if r.tenant_id == tid],
            key=lambda r: (r.priority, r.updated_at or ""),
        )

    def compile(self, rule_id: str, *, tenant_id: str) -> tuple[NotificationRule, Rule]:
        row = self.get(rule_id, tenant_id=tenant_id)
        if row is None:
            raise NotificationRuleError("notification rule not found")
        return row, compile_notification_rule(row)

    def route(
        self,
        *,
        tenant_id: str,
        event_type: str,
        payload: dict[str, Any] | None = None,
        entity_id: str = "event",
    ) -> NotificationRoutingResult:
        rules = self.list_for_tenant(tenant_id=tenant_id)
        return route_notification_event(
            rules,
            event_type=event_type,
            payload=payload,
            entity_id=entity_id,
        )


DEFAULT_NOTIFICATION_RULES_STORE = MemNotificationRulesStore()
