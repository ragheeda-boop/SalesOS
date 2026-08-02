"""STORY-11-09 — Sequencing Engine (email channel, Task/Activity bindings)."""

from __future__ import annotations

import pytest

from app.modules.gtm.sequencing import SequencingError, normalize_steps
from app.modules.gtm.sequencing_store import MemSequencingStore


def test_rejects_non_email_channel() -> None:
    with pytest.raises(SequencingError, match="email-only"):
        normalize_steps([{"subject": "Hi", "body": "x", "channel": "linkedin", "day_offset": 0}])


def test_enroll_advance_binds_task_and_activity() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="Intro sequence",
        steps=[
            {"subject": "Hello", "body": "Day 0", "day_offset": 0},
            {"subject": "Follow up", "body": "Day 3", "day_offset": 3},
        ],
    )
    enr = store.enroll(
        tenant_id="t1",
        sequence_id=seq.id,
        contact_email="prospect@acme.sa",
    )
    assert enr.status == "active"
    assert enr.step_states[0].status == "due"
    assert enr.as_dict()["bound_to_task_activity"] is True

    enr = store.advance(enr.id, tenant_id="t1")
    assert len(enr.task_bindings) == 1
    assert len(enr.activity_bindings) == 1
    assert enr.task_bindings[0].source == "sequence"
    assert enr.activity_bindings[0].kind == "email_sequence_step"
    assert enr.step_states[0].status == "sent"
    assert enr.step_states[1].status == "due"
    assert enr.current_step_index == 1

    enr = store.advance(enr.id, tenant_id="t1")
    assert enr.status == "completed"
    assert len(enr.task_bindings) == 2
    assert len(enr.activity_bindings) == 2


def test_pause_resume_cancel() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="S",
        steps=[{"subject": "A", "body": "b", "day_offset": 0}],
    )
    enr = store.enroll(tenant_id="t1", sequence_id=seq.id, contact_email="a@b.co")
    paused = store.pause(enr.id, tenant_id="t1")
    assert paused.status == "paused"
    with pytest.raises(SequencingError, match="cannot advance"):
        store.advance(enr.id, tenant_id="t1")
    resumed = store.resume(enr.id, tenant_id="t1")
    assert resumed.status == "active"
    cancelled = store.cancel(enr.id, tenant_id="t1")
    assert cancelled.status == "cancelled"
    assert cancelled.step_states[0].status == "skipped"


def test_tenant_isolation() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="S",
        steps=[{"subject": "A", "body": "b"}],
    )
    assert store.get_definition(seq.id, tenant_id="t2") is None
    enr = store.enroll(tenant_id="t1", sequence_id=seq.id, contact_email="a@b.co")
    assert store.get_enrollment(enr.id, tenant_id="t2") is None
    assert store.list_enrollments(tenant_id="t2") == []


def test_invalid_email_rejected() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="S",
        steps=[{"subject": "A", "body": "b"}],
    )
    with pytest.raises(SequencingError, match="contact_email"):
        store.enroll(tenant_id="t1", sequence_id=seq.id, contact_email="not-an-email")
