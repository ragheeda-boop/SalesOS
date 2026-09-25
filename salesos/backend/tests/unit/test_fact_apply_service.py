from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.modules.facts.apply_service import (
    FactApplyRejected,
    FactApplyService,
    _coerce_value,
)


class _Result:
    def __init__(self, value):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class _Session:
    def __init__(self, tenant, fact, target):
        self.values = [_Result(tenant), _Result(fact), _Result(target)]
        self.events = []

    async def execute(self, _statement):
        return self.values.pop(0)

    def add(self, value):
        self.events.append(value)


def _fact(*, status="APPROVED", field_name="city", value="Riyadh"):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=TENANT,
        subject_type="company",
        subject_id=SUBJECT,
        field_name=field_name,
        proposed_value=value,
        status=status,
        reviewer_id="reviewer-1",
        reviewed_at=datetime.now(UTC),
        applied_at=None,
    )


TENANT = uuid4()
SUBJECT = uuid4()


@pytest.mark.asyncio
async def test_apply_requires_approved_fact_and_is_atomic_at_service_boundary():
    fact = _fact()
    target = SimpleNamespace(city="Jeddah")
    session = _Session(str(TENANT), fact, target)

    result = await FactApplyService(session).apply(
        tenant_id=TENANT,
        fact_id=fact.id,
        actor_id="reviewer-1",
        reason="Human review confirmed the city.",
    )

    assert result.changed is True
    assert result.status == "APPLIED"
    assert target.city == "Riyadh"
    assert fact.status == "APPLIED"
    assert fact.applied_at is not None
    assert len(session.events) == 1
    assert session.events[0].event_type == "FACT_APPLIED"


@pytest.mark.asyncio
async def test_apply_rejects_proposed_and_identity_fields():
    fact = _fact(status="PROPOSED")
    session = _Session(str(TENANT), fact, SimpleNamespace(city="Jeddah"))
    with pytest.raises(FactApplyRejected, match="only human-approved"):
        await FactApplyService(session).apply(
            tenant_id=TENANT,
            fact_id=fact.id,
            actor_id="reviewer-1",
            reason="not approved",
        )

    assert _coerce_value("employees_count", 12) == 12
    with pytest.raises(FactApplyRejected, match="not allowlisted"):
        bad = _fact(field_name="cr_number", value="101")
        bad_session = _Session(str(TENANT), bad, SimpleNamespace(city="Jeddah"))
        await FactApplyService(bad_session).apply(
            tenant_id=TENANT,
            fact_id=bad.id,
            actor_id="reviewer-1",
            reason="identity fields require Phase 7 review",
        )


def test_apply_value_types_are_strict():
    with pytest.raises(FactApplyRejected):
        _coerce_value("employees_count", "12")
    with pytest.raises(FactApplyRejected):
        _coerce_value("incorporation_date", "not-a-date")
