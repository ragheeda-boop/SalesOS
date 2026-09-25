"""Proposal-only FactRecorder service.

The caller owns the AsyncSession transaction and tenant GUC. This service
records evidence and a review proposal atomically, but never mutates Company or
Contact. Applying an approved fact remains a separate, currently unavailable
capability until field ownership and transactional application are implemented.
"""

from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.company.models import Company
from app.modules.contact.models import Contact
from app.modules.facts.models import (
    CanonicalFact,
    CanonicalFactEvent,
    EvidenceRecord,
    FactEvidence,
)
from domains.commercial.evidence.contracts.models import EvidenceItem, EvidenceKind
from domains.commercial.evidence.engine.scoring import (
    AGENT_UPDATABLE_FACT_FIELDS,
    PROTECTED_FACT_FIELDS,
    REVIEW_ONLY_FACT_FIELDS,
    decide_fact,
    score_evidence,
)


class FactProposalError(ValueError):
    """Base error for a proposal that fails its policy or persistence contract."""


class FactPolicyRejected(FactProposalError):
    """The proposal is unsupported, unsafe, or outside the approved field set."""


class DismissedValueBlocked(FactProposalError):
    """A human previously dismissed this exact tenant/entity/field/value tuple."""


class IdempotencyConflict(FactProposalError):
    """An idempotency key was reused for a different proposal payload."""


class DuplicateOpenProposal(FactProposalError):
    """An equivalent proposal is already awaiting review under another key."""


@dataclass(frozen=True)
class ProposalPlan:
    tenant_id: uuid.UUID
    subject_type: str
    subject_id: uuid.UUID
    field_name: str
    proposed_value: Any
    value_hash: str
    evidence_hashes: tuple[str, ...]
    evidence_snapshot: tuple[dict[str, Any], ...]
    score: float
    evidence_band: str
    decision_reason: str
    idempotency_key: str
    request_fingerprint: str
    actor_type: str
    actor_id: str | None


@dataclass(frozen=True)
class FactProposalResult:
    fact_id: uuid.UUID
    status: str
    score: float
    evidence_band: str
    decision_reason: str
    created: bool


def _canonical_json(value: Any) -> str:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as exc:
        raise FactPolicyRejected("proposal and evidence data must be finite JSON values") from exc


def _sha256(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _evidence_snapshot(item: EvidenceItem) -> dict[str, Any]:
    assert item.evidence_kind is not None
    return {
        "id": str(item.id),
        "evidence_type": item.evidence_type.value,
        "evidence_kind": item.evidence_kind.value,
        "source": {
            "source_domain": item.source.source_domain,
            "source_type": item.source.source_type,
            "source_id": item.source.source_id or None,
            "source_name": item.source.source_name or None,
        },
        "description": item.description,
        "confidence": item.confidence,
        "confidence_level": item.confidence_level.value,
        "data": item.data,
        "recorded_at": item.recorded_at.isoformat(),
    }


def prepare_proposal(
    *,
    tenant_id: str | uuid.UUID,
    subject_type: str,
    subject_id: str | uuid.UUID,
    field_name: str,
    proposed_value: Any,
    evidence: list[EvidenceItem],
    idempotency_token: str,
    actor_type: str,
    actor_id: str | None,
) -> ProposalPlan:
    """Validate and fingerprint a proposal without database access."""
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
        subject_uuid = uuid.UUID(str(subject_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FactPolicyRejected("tenant_id and subject_id must be UUIDs") from exc

    if subject_type not in {"company", "contact"}:
        raise FactPolicyRejected("subject_type must be company or contact")
    if (
        not isinstance(idempotency_token, str)
        or not idempotency_token.strip()
        or len(idempotency_token) > 255
    ):
        raise FactPolicyRejected("idempotency_token is required and must be at most 255 characters")
    if actor_type not in {"human", "agent", "system"}:
        raise FactPolicyRejected("actor_type must be human, agent, or system")
    if actor_type == "human" and not actor_id:
        raise FactPolicyRejected("human proposals require a verified actor_id")
    if field_name in PROTECTED_FACT_FIELDS:
        raise FactPolicyRejected("identity and control fields cannot be proposed by agents")
    if field_name not in AGENT_UPDATABLE_FACT_FIELDS | REVIEW_ONLY_FACT_FIELDS:
        raise FactPolicyRejected("field is not in the explicit ADR-0114 fact field registry")
    target_model = Company if subject_type == "company" else Contact
    if field_name not in target_model.__table__.columns:
        raise FactPolicyRejected(f"field {field_name!r} does not exist on {subject_type}")
    if proposed_value is None:
        raise FactPolicyRejected("empty values cannot be proposed")

    # Validate that both the field value and all evidence payloads are safe for
    # deterministic JSONB persistence before any query or write occurs.
    value_json = _canonical_json(proposed_value)
    if not evidence:
        raise FactPolicyRejected("at least one classified evidence item is required")
    for item in evidence:
        if not isinstance(item.evidence_kind, EvidenceKind):
            raise FactPolicyRejected("every evidence item must have a recognized evidence_kind")
        if not 0 <= item.confidence <= 1:
            raise FactPolicyRejected("evidence confidence must be between 0 and 1")
    snapshots = tuple(_evidence_snapshot(item) for item in evidence)
    evidence_hashes = tuple(_sha256(snapshot) for snapshot in snapshots)

    decision = decide_fact(field_name, evidence)
    if not decision.store:
        raise FactPolicyRejected(decision.reason)
    score = score_evidence(evidence).score

    # Even a VERIFIED decision remains a proposal. This service has no CRM
    # update path; a future apply service needs independent ownership checks.
    reason = f"proposal_only:{decision.reason}"
    value_hash = hashlib.sha256(value_json.encode("utf-8")).hexdigest()
    idempotency_key = hashlib.sha256(
        f"{tenant_uuid}:{idempotency_token.strip()}".encode("utf-8")
    ).hexdigest()
    fingerprint = _sha256(
        {
            "subject_type": subject_type,
            "subject_id": str(subject_uuid),
            "field_name": field_name,
            "value_hash": value_hash,
            "evidence_hashes": sorted(evidence_hashes),
            "actor_type": actor_type,
            "actor_id": actor_id,
        }
    )
    return ProposalPlan(
        tenant_id=tenant_uuid,
        subject_type=subject_type,
        subject_id=subject_uuid,
        field_name=field_name,
        proposed_value=json.loads(value_json),
        value_hash=value_hash,
        evidence_hashes=evidence_hashes,
        evidence_snapshot=snapshots,
        score=score,
        evidence_band=decision.band.value,
        decision_reason=reason,
        idempotency_key=idempotency_key,
        request_fingerprint=fingerprint,
        actor_type=actor_type,
        actor_id=actor_id,
    )


class FactProposalService:
    """Persist one immutable evidence bundle and one review-only fact proposal."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def propose(
        self,
        *,
        tenant_id: str | uuid.UUID,
        subject_type: str,
        subject_id: str | uuid.UUID,
        field_name: str,
        proposed_value: Any,
        evidence: list[EvidenceItem],
        idempotency_token: str,
        actor_type: str,
        actor_id: str | None,
    ) -> FactProposalResult:
        plan = prepare_proposal(
            tenant_id=tenant_id,
            subject_type=subject_type,
            subject_id=subject_id,
            field_name=field_name,
            proposed_value=proposed_value,
            evidence=evidence,
            idempotency_token=idempotency_token,
            actor_type=actor_type,
            actor_id=actor_id,
        )
        current_tenant = (
            await self.session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        ).scalar_one_or_none()
        if current_tenant != str(plan.tenant_id):
            raise FactPolicyRejected("tenant_id must match the authenticated database tenant scope")
        target_model = Company if subject_type == "company" else Contact
        target_id = (
            await self.session.execute(
                select(target_model.id).where(
                    target_model.id == plan.subject_id,
                    target_model.tenant_id == plan.tenant_id,
                )
            )
        ).scalar_one_or_none()
        if target_id is None:
            raise FactPolicyRejected("CRM subject does not exist in the authenticated tenant")

        idempotent = await self._find_by_idempotency(plan)
        if idempotent is not None:
            self._assert_same_request(idempotent, plan)
            return self._result(idempotent, created=False)

        dismissed = await self._find_value(plan, status="DISMISSED")
        if dismissed is not None:
            raise DismissedValueBlocked("this exact value was previously dismissed by a reviewer")

        pending = await self._find_value(plan, status="PROPOSED")
        if pending is not None:
            raise DuplicateOpenProposal(
                "an equivalent value is already awaiting review; include all evidence in one proposal bundle"
            )

        fact_id = uuid.uuid4()
        fact_values = {
            "id": fact_id,
            "tenant_id": plan.tenant_id,
            "subject_type": plan.subject_type,
            "subject_id": plan.subject_id,
            "field_name": plan.field_name,
            "proposed_value": plan.proposed_value,
            "value_hash": plan.value_hash,
            "status": "PROPOSED",
            "evidence_band": plan.evidence_band,
            "score": plan.score,
            "decision_reason": plan.decision_reason,
            "idempotency_key": plan.idempotency_key,
            "request_fingerprint": plan.request_fingerprint,
            "actor_type": plan.actor_type,
            "actor_id": plan.actor_id,
            "evidence_snapshot": list(plan.evidence_snapshot),
        }
        inserted_fact_id = (
            await self.session.execute(
                pg_insert(CanonicalFact)
                .values(**fact_values)
                .on_conflict_do_nothing()
                .returning(CanonicalFact.id)
            )
        ).scalar_one_or_none()
        if inserted_fact_id is None:
            # Another transaction won an idempotency/open/dismissed uniqueness
            # race. PostgreSQL's ON CONFLICT leaves this transaction usable.
            idempotent = await self._find_by_idempotency(plan)
            if idempotent is not None:
                self._assert_same_request(idempotent, plan)
                return self._result(idempotent, created=False)
            dismissed = await self._find_value(plan, status="DISMISSED")
            if dismissed is not None:
                raise DismissedValueBlocked("this exact value was dismissed concurrently")
            pending = await self._find_value(plan, status="PROPOSED")
            if pending is not None:
                raise DuplicateOpenProposal("an equivalent proposal was created concurrently")
            raise FactProposalError(
                "proposal insert conflicted with an unrecognized uniqueness constraint"
            )

        evidence_ids = [
            await self._upsert_evidence(plan, item, digest)
            for item, digest in zip(evidence, plan.evidence_hashes, strict=True)
        ]
        for evidence_id in evidence_ids:
            await self.session.execute(
                pg_insert(FactEvidence)
                .values(
                    id=uuid.uuid4(),
                    tenant_id=plan.tenant_id,
                    fact_id=inserted_fact_id,
                    evidence_id=evidence_id,
                    relation="SUPPORTS",
                )
                .on_conflict_do_nothing()
            )
        await self.session.execute(
            pg_insert(CanonicalFactEvent).values(
                id=uuid.uuid4(),
                tenant_id=plan.tenant_id,
                fact_id=inserted_fact_id,
                event_type="PROPOSED",
                from_status=None,
                to_status="PROPOSED",
                actor_type=plan.actor_type,
                actor_id=plan.actor_id,
                reason=plan.decision_reason,
                event_data={"evidence_count": len(evidence_ids), "field_name": plan.field_name},
            )
        )
        return FactProposalResult(
            fact_id=inserted_fact_id,
            status="PROPOSED",
            score=plan.score,
            evidence_band=plan.evidence_band,
            decision_reason=plan.decision_reason,
            created=True,
        )

    async def _upsert_evidence(
        self,
        plan: ProposalPlan,
        item: EvidenceItem,
        digest: str,
    ) -> uuid.UUID:
        evidence_id = uuid.uuid4()
        result = await self.session.execute(
            pg_insert(EvidenceRecord)
            .values(
                id=evidence_id,
                tenant_id=plan.tenant_id,
                source_domain=item.source.source_domain,
                source_type=item.source.source_type,
                source_id=item.source.source_id or None,
                source_name=item.source.source_name or None,
                evidence_kind=item.evidence_kind.value,
                description=item.description,
                confidence=item.confidence,
                data=item.data,
                evidence_hash=digest,
                observed_at=item.recorded_at,
            )
            .on_conflict_do_nothing()
            .returning(EvidenceRecord.id)
        )
        stored_id = result.scalar_one_or_none()
        if stored_id is not None:
            return stored_id
        existing = (
            await self.session.execute(
                select(EvidenceRecord.id).where(
                    EvidenceRecord.tenant_id == plan.tenant_id,
                    EvidenceRecord.evidence_hash == digest,
                )
            )
        ).scalar_one_or_none()
        if existing is None:
            raise FactProposalError("evidence uniqueness conflict could not be resolved")
        return existing

    async def _find_by_idempotency(self, plan: ProposalPlan) -> CanonicalFact | None:
        return (
            await self.session.execute(
                select(CanonicalFact).where(
                    CanonicalFact.tenant_id == plan.tenant_id,
                    CanonicalFact.idempotency_key == plan.idempotency_key,
                )
            )
        ).scalar_one_or_none()

    async def _find_value(self, plan: ProposalPlan, *, status: str) -> CanonicalFact | None:
        return (
            await self.session.execute(
                select(CanonicalFact).where(
                    CanonicalFact.tenant_id == plan.tenant_id,
                    CanonicalFact.subject_type == plan.subject_type,
                    CanonicalFact.subject_id == plan.subject_id,
                    CanonicalFact.field_name == plan.field_name,
                    CanonicalFact.value_hash == plan.value_hash,
                    CanonicalFact.status == status,
                )
            )
        ).scalar_one_or_none()

    @staticmethod
    def _assert_same_request(existing: CanonicalFact, plan: ProposalPlan) -> None:
        if existing.request_fingerprint != plan.request_fingerprint:
            raise IdempotencyConflict("idempotency token was already used for a different proposal")

    @staticmethod
    def _result(fact: CanonicalFact, *, created: bool) -> FactProposalResult:
        return FactProposalResult(
            fact_id=fact.id,
            status=fact.status,
            score=fact.score,
            evidence_band=fact.evidence_band,
            decision_reason=fact.decision_reason,
            created=created,
        )
