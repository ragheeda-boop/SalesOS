"""State-transition policy tests for the canonical fact review boundary."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.modules.facts.review_service import (
    FactReviewService,
    FactTransitionRejected,
    normalize_review_request,
)

TENANT = uuid.UUID("ab09529e-3e80-413b-af35-d06bf70471cd")
FACT = uuid.UUID("9d564718-f301-40b8-9b42-8fd48fd75c8a")


class Result:
    def __init__(self, value: Any = None):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class ScriptedSession:
    def __init__(self, query_results: list[Any]):
        self.query_results = list(query_results)
        self.added: list[Any] = []

    async def execute(self, statement):
        if not self.query_results:
            raise AssertionError("unexpected database query")
        return Result(self.query_results.pop(0))

    def add(self, instance):
        self.added.append(instance)


def run(coro):
    return asyncio.run(coro)


def decide(session: ScriptedSession, *, decision: str = "approve"):
    return run(
        FactReviewService(session).decide(
            tenant_id=TENANT,
            fact_id=FACT,
            decision=decision,
            reviewer_id="verified-user-42",
            reason="Confirmed against the authoritative record.",
        )
    )


@pytest.mark.parametrize(
    ("decision", "status"),
    [("approve", "APPROVED"), ("reject", "REJECTED"), ("dismiss", "DISMISSED")],
)
def test_normalize_review_maps_only_explicit_decisions(decision, status):
    tenant, fact, parsed, reviewer, reason = normalize_review_request(
        tenant_id=TENANT,
        fact_id=FACT,
        decision=decision,
        reviewer_id=" reviewer-42 ",
        reason=" confirmed ",
    )
    assert tenant == TENANT and fact == FACT
    assert parsed.value == decision
    assert reviewer == "reviewer-42" and reason == "confirmed"
    assert {"approve": "APPROVED", "reject": "REJECTED", "dismiss": "DISMISSED"}[decision] == status


def test_invalid_decision_identity_and_empty_reason_fail_closed():
    payload = {
        "tenant_id": TENANT,
        "fact_id": FACT,
        "decision": "approve",
        "reviewer_id": "verified-user-42",
        "reason": "confirmed",
    }
    for update in (
        {"decision": "apply"},
        {"reviewer_id": "  "},
        {"reason": "  "},
        {"fact_id": "not-a-uuid"},
    ):
        with pytest.raises(FactTransitionRejected):
            normalize_review_request(**(payload | update))


def test_review_transition_is_single_and_replay_is_idempotent():
    fact = SimpleNamespace(
        id=FACT,
        status="PROPOSED",
        actor_type="agent",
        actor_id="agent-run-1",
        reviewer_id=None,
        reviewed_at=None,
    )
    writer = ScriptedSession([str(TENANT), fact])
    first = decide(writer)
    assert first.status == "APPROVED" and first.changed is True
    assert fact.reviewer_id == "verified-user-42"
    assert len(writer.added) == 1
    event = writer.added[0]
    assert event.event_type == "REVIEW_DECIDED"
    assert event.from_status == "PROPOSED" and event.to_status == "APPROVED"
    assert event.actor_type == "human"

    replay = ScriptedSession([str(TENANT), fact, event])
    second = decide(replay)
    assert second.status == "APPROVED" and second.changed is False
    assert replay.added == []


def test_review_rejects_wrong_tenant_and_non_pending_fact():
    mismatch = ScriptedSession(["fc3c6919-4ea2-4722-8f4e-d9cba35ac861"])
    with pytest.raises(FactTransitionRejected, match="authenticated database tenant"):
        decide(mismatch)

    decided = SimpleNamespace(
        id=FACT,
        status="REJECTED",
        reviewer_id="reviewer-old",
        reviewed_at=datetime.now(UTC),
    )
    session = ScriptedSession([str(TENANT), decided])
    with pytest.raises(FactTransitionRejected, match="different review decision"):
        decide(session)


def test_human_proposer_cannot_review_their_own_fact():
    fact = SimpleNamespace(
        id=FACT,
        status="PROPOSED",
        actor_type="human",
        actor_id="verified-user-42",
        reviewer_id=None,
        reviewed_at=None,
    )
    session = ScriptedSession([str(TENANT), fact])
    with pytest.raises(FactTransitionRejected, match="cannot review their own"):
        decide(session)


def test_conflicting_retry_cannot_change_a_human_decision():
    fact = SimpleNamespace(id=FACT, status="APPROVED", reviewer_id="verified-user-42")
    event = SimpleNamespace(
        event_type="REVIEW_DECIDED",
        to_status="APPROVED",
        actor_id="verified-user-42",
        reason="Confirmed against the authoritative record.",
        created_at=datetime.now(UTC),
    )
    session = ScriptedSession([str(TENANT), fact, event])
    with pytest.raises(FactTransitionRejected, match="different review decision"):
        decide(session, decision="reject")
    assert session.added == []
