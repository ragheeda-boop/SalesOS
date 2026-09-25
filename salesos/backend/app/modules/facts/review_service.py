"""Human review transitions for proposal-only canonical facts."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.facts.models import CanonicalFact, CanonicalFactEvent


class FactReviewError(ValueError):
    """Base error for a fact review that fails its state or scope contract."""


class FactReviewNotFound(FactReviewError):
    """The fact is not visible in the authenticated tenant."""


class FactTransitionRejected(FactReviewError):
    """The requested decision is not valid for the fact's current state."""


class ReviewDecision(StrEnum):
    APPROVE = "approve"
    REJECT = "reject"
    DISMISS = "dismiss"


_TARGET_STATUS = {
    ReviewDecision.APPROVE: "APPROVED",
    ReviewDecision.REJECT: "REJECTED",
    ReviewDecision.DISMISS: "DISMISSED",
}


@dataclass(frozen=True)
class FactReviewResult:
    fact_id: uuid.UUID
    status: str
    reviewed_at: datetime
    changed: bool


def normalize_review_request(
    *,
    tenant_id: str | uuid.UUID,
    fact_id: str | uuid.UUID,
    decision: str | ReviewDecision,
    reviewer_id: str,
    reason: str,
) -> tuple[uuid.UUID, uuid.UUID, ReviewDecision, str, str]:
    """Validate the review payload before performing any database work."""
    try:
        tenant_uuid = uuid.UUID(str(tenant_id))
        fact_uuid = uuid.UUID(str(fact_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise FactTransitionRejected("tenant_id and fact_id must be UUIDs") from exc

    try:
        review_decision = ReviewDecision(decision)
    except (ValueError, TypeError) as exc:
        raise FactTransitionRejected("decision must be approve, reject, or dismiss") from exc

    if not isinstance(reviewer_id, str) or not reviewer_id.strip() or len(reviewer_id) > 128:
        raise FactTransitionRejected("reviewer_id must be a verified non-empty identity")
    if not isinstance(reason, str) or not reason.strip() or len(reason) > 2000:
        raise FactTransitionRejected("a review reason is required (maximum 2000 characters)")

    return tenant_uuid, fact_uuid, review_decision, reviewer_id.strip(), reason.strip()


class FactReviewService:
    """Apply one human decision to a proposal; never update the CRM entity."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def list_proposals(
        self,
        *,
        tenant_id: str | uuid.UUID,
        status: str = "PROPOSED",
        limit: int = 50,
        offset: int = 0,
    ) -> list[CanonicalFact]:
        try:
            tenant_uuid = uuid.UUID(str(tenant_id))
        except (ValueError, TypeError, AttributeError) as exc:
            raise FactTransitionRejected("tenant_id must be a UUID") from exc
        allowed_statuses = {
            "PROPOSED",
            "APPROVED",
            "REJECTED",
            "DISMISSED",
            "APPLIED",
            "SUPERSEDED",
            "STALE",
        }
        if status not in allowed_statuses:
            raise FactTransitionRejected("unsupported fact status filter")
        if not 1 <= limit <= 100 or not 0 <= offset <= 100_000:
            raise FactTransitionRejected("limit must be 1-100 and offset must be 0-100000")
        current_tenant = (
            await self.session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        ).scalar_one_or_none()
        if current_tenant != str(tenant_uuid):
            raise FactTransitionRejected(
                "tenant_id must match the authenticated database tenant scope"
            )
        return list(
            (
                await self.session.execute(
                    select(CanonicalFact)
                    .where(
                        CanonicalFact.tenant_id == tenant_uuid,
                        CanonicalFact.status == status,
                    )
                    .order_by(CanonicalFact.created_at.desc(), CanonicalFact.id.desc())
                    .limit(limit)
                    .offset(offset)
                )
            )
            .scalars()
            .all()
        )

    async def decide(
        self,
        *,
        tenant_id: str | uuid.UUID,
        fact_id: str | uuid.UUID,
        decision: str | ReviewDecision,
        reviewer_id: str,
        reason: str,
    ) -> FactReviewResult:
        tenant_uuid, fact_uuid, review_decision, actor_id, normalized_reason = (
            normalize_review_request(
                tenant_id=tenant_id,
                fact_id=fact_id,
                decision=decision,
                reviewer_id=reviewer_id,
                reason=reason,
            )
        )
        current_tenant = (
            await self.session.execute(text("SELECT current_setting('app.tenant_id', true)"))
        ).scalar_one_or_none()
        if current_tenant != str(tenant_uuid):
            raise FactTransitionRejected(
                "tenant_id must match the authenticated database tenant scope"
            )

        fact = (
            await self.session.execute(
                select(CanonicalFact)
                .where(CanonicalFact.id == fact_uuid, CanonicalFact.tenant_id == tenant_uuid)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if fact is None:
            raise FactReviewNotFound("fact proposal not found in the authenticated tenant")

        target_status = _TARGET_STATUS[review_decision]
        if fact.status == target_status:
            latest_event = (
                await self.session.execute(
                    select(CanonicalFactEvent)
                    .where(
                        CanonicalFactEvent.tenant_id == tenant_uuid,
                        CanonicalFactEvent.fact_id == fact_uuid,
                        CanonicalFactEvent.event_type == "REVIEW_DECIDED",
                    )
                    .order_by(
                        CanonicalFactEvent.created_at.desc(),
                        CanonicalFactEvent.id.desc(),
                    )
                    .limit(1)
                )
            ).scalar_one_or_none()
            if (
                latest_event is not None
                and latest_event.event_type == "REVIEW_DECIDED"
                and latest_event.to_status == target_status
                and latest_event.actor_id == actor_id
                and latest_event.reason == normalized_reason
            ):
                if fact.reviewed_at is None:
                    raise FactTransitionRejected("reviewed fact is missing its review timestamp")
                return FactReviewResult(
                    fact_id=fact.id,
                    status=fact.status,
                    reviewed_at=fact.reviewed_at,
                    changed=False,
                )
            raise FactTransitionRejected("fact already has a different review decision")

        if fact.status != "PROPOSED":
            if fact.status in _TARGET_STATUS.values():
                raise FactTransitionRejected("fact already has a different review decision")
            raise FactTransitionRejected(
                f"cannot decide a fact in {fact.status!r}; only PROPOSED facts are reviewable"
            )
        if fact.actor_type == "human" and fact.actor_id == actor_id:
            raise FactTransitionRejected("the proposer cannot review their own fact")

        reviewed_at = datetime.now(UTC)
        fact.status = target_status
        fact.reviewer_id = actor_id
        fact.reviewed_at = reviewed_at
        self.session.add(
            CanonicalFactEvent(
                tenant_id=tenant_uuid,
                fact_id=fact_uuid,
                event_type="REVIEW_DECIDED",
                from_status="PROPOSED",
                to_status=target_status,
                actor_type="human",
                actor_id=actor_id,
                reason=normalized_reason,
                event_data={"decision": review_decision.value},
            )
        )
        return FactReviewResult(
            fact_id=fact.id,
            status=target_status,
            reviewed_at=reviewed_at,
            changed=True,
        )
