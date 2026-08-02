"""STORY-11-09 / 11-09b — Sequencing (email + LinkedIn + WhatsApp partner APIs)."""

from __future__ import annotations

import pytest

from app.modules.gtm.sequence_channels import assert_compliant_mode
from app.modules.gtm.sequencing import SequencingError, normalize_steps
from app.modules.gtm.sequencing_store import MemSequencingStore


def test_rejects_unknown_channel() -> None:
    with pytest.raises(SequencingError, match="unsupported channel"):
        normalize_steps([{"subject": "Hi", "body": "x", "channel": "telegram", "day_offset": 0}])


def test_rejects_tos_risk_automation_mode() -> None:
    with pytest.raises(SequencingError, match="forbidden channel mode"):
        assert_compliant_mode("browser_automation")


@pytest.mark.asyncio
async def test_enroll_advance_binds_task_and_activity() -> None:
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

    enr = await store.advance(enr.id, tenant_id="t1")
    assert len(enr.task_bindings) == 1
    assert len(enr.activity_bindings) == 1
    assert enr.task_bindings[0].source == "sequence"
    assert enr.activity_bindings[0].kind == "email_sequence_step"
    assert enr.step_states[0].status == "sent"
    assert enr.step_states[1].status == "due"
    assert enr.current_step_index == 1

    enr = await store.advance(enr.id, tenant_id="t1")
    assert enr.status == "completed"
    assert len(enr.task_bindings) == 2
    assert len(enr.activity_bindings) == 2


@pytest.mark.asyncio
async def test_linkedin_whatsapp_partner_channels() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="Multi",
        steps=[
            {"subject": "Email", "body": "e", "channel": "email", "day_offset": 0},
            {
                "subject": "LI note",
                "body": "connect",
                "channel": "linkedin",
                "day_offset": 1,
            },
            {
                "subject": "WA",
                "body": "hello",
                "channel": "whatsapp",
                "day_offset": 2,
            },
        ],
    )
    assert seq.channel == "multi"
    enr = store.enroll(
        tenant_id="t1",
        sequence_id=seq.id,
        contact_email="a@b.co",
        contact_handles={
            "linkedin": "urn:li:person:abc",
            "whatsapp": "+966501234567",
        },
    )
    enr = await store.advance(enr.id, tenant_id="t1")
    assert enr.last_send["channel"] == "email"
    enr = await store.advance(enr.id, tenant_id="t1")
    assert enr.last_send["channel"] == "linkedin"
    assert enr.activity_bindings[-1].kind == "linkedin_sequence_step"
    enr = await store.advance(enr.id, tenant_id="t1")
    assert enr.last_send["channel"] == "whatsapp"
    assert enr.status == "completed"


@pytest.mark.asyncio
async def test_linkedin_requires_partner_urn() -> None:
    store = MemSequencingStore()
    seq = store.create_definition(
        tenant_id="t1",
        name="LI",
        steps=[{"subject": "Hi", "body": "x", "channel": "linkedin", "day_offset": 0}],
    )
    enr = store.enroll(tenant_id="t1", sequence_id=seq.id, contact_email="a@b.co")
    with pytest.raises(SequencingError, match="linkedin"):
        await store.advance(enr.id, tenant_id="t1")


@pytest.mark.asyncio
async def test_pause_resume_cancel() -> None:
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
        await store.advance(enr.id, tenant_id="t1")
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
