"""Policy and persistence-shape tests for the review-only FactRecorder."""

from __future__ import annotations

import asyncio
import uuid
from datetime import UTC, datetime
from types import SimpleNamespace
from typing import Any

import pytest

from app.modules.facts.service import (
    DismissedValueBlocked,
    DuplicateOpenProposal,
    FactPolicyRejected,
    FactProposalService,
    IdempotencyConflict,
    prepare_proposal,
)
from domains.commercial.evidence.contracts.models import (
    ConfidenceLevel,
    EvidenceItem,
    EvidenceKind,
    EvidenceSource,
    EvidenceType,
)

TENANT = uuid.UUID("ab09529e-3e80-413b-af35-d06bf70471cd")
COMPANY = uuid.UUID("245931eb-c34d-49d4-a0d1-65e0ab0e3415")
FACT = uuid.UUID("9d564718-f301-40b8-9b42-8fd48fd75c8a")
EVIDENCE = uuid.UUID("b197f625-615e-4267-b5d4-a6b3b7fdf064")


def evidence(kind: EvidenceKind | None = EvidenceKind.OFFICIAL_REGISTRY) -> EvidenceItem:
    return EvidenceItem(
        id="source-record-42",
        evidence_type=EvidenceType.MARKET_SIGNAL,
        source=EvidenceSource("registry", "official_record", "reg:42", "Registry"),
        description="Official record lists the company in Riyadh.",
        confidence=0.01,  # Informational; the explicit kind determines ADR-0113 score.
        confidence_level=ConfidenceLevel.HIGH,
        evidence_kind=kind,
        data={"city": "Riyadh"},
        recorded_at=datetime(2026, 9, 21, tzinfo=UTC),
    )


def prepare(**overrides: Any):
    args = {
        "tenant_id": TENANT,
        "subject_type": "company",
        "subject_id": COMPANY,
        "field_name": "city",
        "proposed_value": "Riyadh",
        "evidence": [evidence()],
        "idempotency_token": "fact-test-001",
        "actor_type": "agent",
        "actor_id": "agent-run-42",
    }
    args.update(overrides)
    return prepare_proposal(**args)


def test_verified_fact_stays_a_proposal_and_scores_from_kind() -> None:
    plan = prepare()
    assert plan.score == 0.98
    assert plan.evidence_band == "verified"
    assert plan.decision_reason.startswith("proposal_only:")
    assert len(plan.value_hash) == len(plan.idempotency_key) == 64
    assert plan.evidence_snapshot[0]["evidence_kind"] == EvidenceKind.OFFICIAL_REGISTRY.value


def test_unknown_field_unclassified_evidence_and_non_json_values_fail_closed() -> None:
    with pytest.raises(FactPolicyRejected, match="explicit ADR-0114"):
        prepare(field_name="name_en")
    with pytest.raises(FactPolicyRejected, match="recognized evidence_kind"):
        prepare(evidence=[evidence(None)])
    with pytest.raises(FactPolicyRejected, match="finite JSON"):
        prepare(proposed_value=float("nan"))


def test_review_only_cr_can_be_proposed_without_auto_apply() -> None:
    plan = prepare(field_name="cr_number", proposed_value="1010123456")
    assert plan.evidence_band == "verified"
    assert plan.decision_reason.startswith("proposal_only:")


def test_idempotency_fingerprint_covers_scope_and_payload() -> None:
    first = prepare()
    same = prepare()
    changed_value = prepare(proposed_value="Jeddah")
    other_tenant = prepare(tenant_id=uuid.UUID("fc3c6919-4ea2-4722-8f4e-d9cba35ac861"))
    assert first.idempotency_key == same.idempotency_key
    assert first.request_fingerprint == same.request_fingerprint
    assert first.request_fingerprint != changed_value.request_fingerprint
    assert first.idempotency_key != other_tenant.idempotency_key


class Result:
    def __init__(self, value: Any = None):
        self.value = value

    def scalar_one_or_none(self):
        return self.value


class ScriptedSession:
    """Session double; deliberately performs no SQL or external I/O."""

    def __init__(self, query_results: list[Any]):
        self.query_results = list(query_results)
        self.inserted_tables: list[str] = []

    async def execute(self, statement):
        if getattr(statement, "is_insert", False):
            table = statement.table.name
            self.inserted_tables.append(table)
            return Result(
                EVIDENCE
                if table == "evidence_records"
                else FACT
                if table == "canonical_facts"
                else None
            )
        if not self.query_results:
            raise AssertionError("unexpected database query")
        return Result(self.query_results.pop(0))


def run(coro):
    return asyncio.run(coro)


def _propose(session: ScriptedSession, *, token: str = "persist-001"):
    return run(
        FactProposalService(session).propose(
            tenant_id=TENANT,
            subject_type="company",
            subject_id=COMPANY,
            field_name="city",
            proposed_value="Riyadh",
            evidence=[evidence()],
            idempotency_token=token,
            actor_type="agent",
            actor_id="agent-run-42",
        )
    )


def test_persistence_writes_only_ledger_tables() -> None:
    session = ScriptedSession([str(TENANT), COMPANY, None, None, None])
    result = _propose(session)
    assert result.fact_id == FACT
    assert result.status == "PROPOSED"
    assert result.created is True
    assert set(session.inserted_tables) == {
        "evidence_records",
        "canonical_facts",
        "fact_evidence",
        "canonical_fact_events",
    }
    assert "companies" not in session.inserted_tables
    assert "contacts" not in session.inserted_tables


@pytest.mark.parametrize(
    ("status", "error"),
    [("DISMISSED", DismissedValueBlocked), ("PROPOSED", DuplicateOpenProposal)],
)
def test_dismissed_and_open_values_block_before_writes(status, error) -> None:
    plan = prepare()
    current = SimpleNamespace(
        id=FACT,
        tenant_id=TENANT,
        subject_type="company",
        subject_id=COMPANY,
        field_name="city",
        value_hash=plan.value_hash,
        status=status,
    )
    queue = [str(TENANT), COMPANY, None]
    queue += [current] if status == "DISMISSED" else [None, current]
    session = ScriptedSession(queue)
    with pytest.raises(error):
        _propose(session, token=f"new-{status.lower()}")
    assert session.inserted_tables == []


def test_reused_idempotency_key_with_different_payload_is_rejected() -> None:
    existing = SimpleNamespace(
        request_fingerprint="f" * 64,
        id=FACT,
        status="PROPOSED",
        score=0.98,
        evidence_band="verified",
        decision_reason="proposal_only:verified_primary_evidence",
    )
    session = ScriptedSession([str(TENANT), COMPANY, existing])
    with pytest.raises(IdempotencyConflict):
        _propose(session)
    assert session.inserted_tables == []


def test_database_tenant_scope_must_match_request_tenant() -> None:
    session = ScriptedSession(["fc3c6919-4ea2-4722-8f4e-d9cba35ac861"])
    with pytest.raises(FactPolicyRejected, match="authenticated database tenant"):
        _propose(session)
    assert session.inserted_tables == []


def test_exact_idempotent_retry_returns_existing_proposal_without_writes() -> None:
    plan = prepare(idempotency_token="persist-001")
    existing = SimpleNamespace(
        request_fingerprint=plan.request_fingerprint,
        id=FACT,
        status="PROPOSED",
        score=0.98,
        evidence_band="verified",
        decision_reason=plan.decision_reason,
    )
    session = ScriptedSession([str(TENANT), COMPANY, existing])
    result = _propose(session)
    assert result.fact_id == FACT
    assert result.created is False
    assert session.inserted_tables == []
