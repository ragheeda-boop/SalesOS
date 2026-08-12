"""Decision Platform (alternate) cross-tenant isolation — EAB DUP-01 residual.

Proves explain + feedback refuse foreign-tenant decision ids without deleting
engines. Does not claim live prod multi-tenant proof or GA GO.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.modules.decision.engine import DecisionEngine
from app.modules.decision.schemas import DecisionContext, Feedback


def _ctx(tenant_id: str, entity_id: str = "co-1") -> DecisionContext:
    return DecisionContext(
        tenant_id=tenant_id,
        actor_id="actor-1",
        entity_id=entity_id,
        entity_type="company",
        company_id=entity_id,
    )


def test_explain_blocked_for_foreign_tenant() -> None:
    engine = DecisionEngine()
    result = engine.evaluate(_ctx("tenant-a"))
    assert engine.explain(result.decision_id, "tenant-a") is not None
    assert engine.explain(result.decision_id, "tenant-b") is None
    assert engine.explain("missing-id", "tenant-a") is None


def test_history_excludes_foreign_tenant() -> None:
    engine = DecisionEngine()
    a = engine.evaluate(_ctx("tenant-a", "co-a"))
    b = engine.evaluate(_ctx("tenant-b", "co-b"))
    a_ids = {item.decision_id for item in engine.get_history("tenant-a")}
    b_ids = {item.decision_id for item in engine.get_history("tenant-b")}
    assert a.decision_id in a_ids
    assert b.decision_id not in a_ids
    assert b.decision_id in b_ids
    assert a.decision_id not in b_ids


def test_feedback_rejected_for_foreign_tenant_decision() -> None:
    engine = DecisionEngine()
    result = engine.evaluate(_ctx("tenant-a"))
    fb_id, ok = engine.submit_feedback(
        Feedback(
            decision_id=result.decision_id,
            tenant_id="tenant-b",
            actor_id="actor-b",
            outcome="accepted",
            timestamp=datetime.now(UTC).isoformat(),
        )
    )
    assert ok is False
    assert fb_id == ""
    own_id, own_ok = engine.submit_feedback(
        Feedback(
            decision_id=result.decision_id,
            tenant_id="tenant-a",
            actor_id="actor-a",
            outcome="accepted",
            timestamp=datetime.now(UTC).isoformat(),
        )
    )
    assert own_ok is True
    assert own_id
