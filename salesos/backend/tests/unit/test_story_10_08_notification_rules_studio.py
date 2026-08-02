"""STORY-10-08 — Notification Rules Studio: routing via RulesEngine."""

from __future__ import annotations

import pytest

from app.modules.rules_engine.models import ActionType
from app.modules.tenant_studio.notification_rules import NotificationRuleError
from app.modules.tenant_studio.notification_rules_engine import (
    compile_notification_rule,
    route_notification_event,
)
from app.modules.tenant_studio.notification_rules_store import MemNotificationRulesStore


def test_upsert_and_route_opportunity_stage() -> None:
    store = MemNotificationRulesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="Stage alert",
        event_type="opportunity.stage_changed",
        channels=["in_app", "email"],
        recipients=[{"kind": "role", "value": "sales_manager"}],
        conditions=[{"field": "stage", "operator": "equals", "value": "proposal"}],
        message_template="Deal {name} moved to {stage}",
        priority=10,
    )
    miss = store.route(
        tenant_id="t1",
        event_type="opportunity.stage_changed",
        payload={"stage": "qualified", "name": "Acme"},
    )
    assert miss.matched is False

    hit = store.route(
        tenant_id="t1",
        event_type="opportunity.stage_changed",
        payload={"stage": "proposal", "name": "Acme"},
    )
    assert hit.matched is True
    assert len(hit.routes) == 1
    assert hit.routes[0].rule_id == rule.id
    assert hit.routes[0].channels == ["in_app", "email"]
    assert hit.routes[0].message == "Deal Acme moved to proposal"
    assert all(
        a.get("action_type") == ActionType.send_notification.value for a in hit.routes[0].actions
    )


def test_compile_produces_send_notification_actions() -> None:
    store = MemNotificationRulesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="Sync fail",
        event_type="sync.failed",
        channels=["in_app"],
        recipients=[{"kind": "user", "value": "u-1"}],
        message_template="Sync failed",
    )
    _, engine = store.compile(rule.id, tenant_id="t1")
    assert engine.enabled is True
    assert len(engine.actions) == 1
    assert engine.actions[0].type == ActionType.send_notification
    assert engine.actions[0].params["channel"] == "in_app"


def test_inactive_rule_does_not_route() -> None:
    store = MemNotificationRulesStore()
    store.upsert(
        tenant_id="t1",
        name="Off",
        event_type="task.overdue",
        channels=["in_app"],
        recipients=[{"kind": "owner", "value": "owner"}],
        active=False,
    )
    result = store.route(tenant_id="t1", event_type="task.overdue", payload={})
    assert result.matched is False


def test_reject_unknown_channel_and_event() -> None:
    store = MemNotificationRulesStore()
    with pytest.raises(NotificationRuleError, match="channel"):
        store.upsert(
            tenant_id="t1",
            name="Bad ch",
            event_type="lead.assigned",
            channels=["sms"],
            recipients=[{"kind": "role", "value": "ae"}],
        )
    with pytest.raises(NotificationRuleError, match="event_type"):
        store.upsert(
            tenant_id="t1",
            name="Bad evt",
            event_type="unknown.event",
            channels=["in_app"],
            recipients=[{"kind": "role", "value": "ae"}],
        )


def test_tenant_isolation() -> None:
    store = MemNotificationRulesStore()
    a = store.upsert(
        tenant_id="tenant-a",
        name="A",
        event_type="score.threshold",
        channels=["email"],
        recipients=[{"kind": "role", "value": "ae"}],
        conditions=[{"field": "score", "operator": "greater_than", "value": 0.8}],
    )
    assert store.get(a.id, tenant_id="tenant-b") is None
    other = store.route(
        tenant_id="tenant-b",
        event_type="score.threshold",
        payload={"score": 0.9},
    )
    assert other.matched is False


def test_priority_orders_routes() -> None:
    store = MemNotificationRulesStore()
    store.upsert(
        tenant_id="t1",
        name="Low",
        event_type="lead.assigned",
        channels=["in_app"],
        recipients=[{"kind": "role", "value": "ae"}],
        priority=50,
    )
    store.upsert(
        tenant_id="t1",
        name="High",
        event_type="lead.assigned",
        channels=["email"],
        recipients=[{"kind": "role", "value": "manager"}],
        priority=1,
    )
    result = route_notification_event(
        store.list_for_tenant(tenant_id="t1"),
        event_type="lead.assigned",
        payload={},
    )
    assert [r.rule_name for r in result.routes] == ["High", "Low"]


def test_compile_standalone() -> None:
    store = MemNotificationRulesStore()
    rule = store.upsert(
        tenant_id="t1",
        name="X",
        event_type="sync.failed",
        channels=["in_app", "email"],
        recipients=[{"kind": "user", "value": "u"}],
    )
    engine = compile_notification_rule(rule)
    assert len(engine.actions) == 2
