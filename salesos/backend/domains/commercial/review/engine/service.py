"""ReviewService — business logic for review workflows.

Handles:
- Creating review requests (deal, quote, proposal, exception)
- Assigning reviewers
- Processing decisions (approve/reject/escalate)
- Querying review status
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from ..contracts.models import Review, ReviewDecision, ReviewStatus, ReviewType
from ..contracts.repository import ReviewRepository


class ReviewService:

    def __init__(self, repository: ReviewRepository, event_bus: Any = None):
        self._repository = repository
        self._event_bus = event_bus

    async def _emit(self, event_type: str, tenant_id: str, data: dict[str, Any]) -> None:
        if not self._event_bus:
            return
        from sdk.events.base import DomainEvent
        event = DomainEvent(event_type=event_type, tenant_id=tenant_id,
                            aggregate_id=data.get("review_id", ""), data=data)
        event.event_type = event_type
        await self._event_bus.publish(event)

    async def create_review(
        self,
        tenant_id: str,
        review_type: ReviewType,
        target_id: str,
        target_type: str,
        requested_by: str = "",
        assigned_to: str = "",
        metadata: dict | None = None,
    ) -> Review:
        review = Review(
            id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            review_type=review_type,
            target_id=target_id,
            target_type=target_type,
            requested_by=requested_by,
            assigned_to=assigned_to,
            metadata=metadata or {},
        )
        result = await self._repository.save(review)
        await self._emit("review.created", tenant_id, {
            "review_id": review.id, "review_type": review_type.value,
            "target_id": target_id, "target_type": target_type,
        })
        return result

    async def assign(self, review_id: str, assigned_to: str) -> Review:
        review = await self._repository.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        if review.is_terminal:
            raise ValueError(f"Cannot assign review in status: {review.status.value}")
        review.assigned_to = assigned_to
        review.status = ReviewStatus.IN_PROGRESS
        review.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(review)
        await self._emit("review.assigned", review.tenant_id, {
            "review_id": review_id, "assigned_to": assigned_to,
        })
        return result

    async def decide(
        self,
        review_id: str,
        decided_by: str,
        decision: str,
        comments: str = "",
    ) -> Review:
        review = await self._repository.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        if review.is_terminal:
            raise ValueError(f"Cannot decide on review in status: {review.status.value}")

        dec = ReviewDecision(
            decision=decision,
            decided_by=decided_by,
            comments=comments,
        )
        review.decisions.append(dec)

        if decision == "approve":
            review.status = ReviewStatus.APPROVED
        elif decision == "reject":
            review.status = ReviewStatus.REJECTED
        elif decision == "escalate":
            review.status = ReviewStatus.ESCALATED
        else:
            raise ValueError(f"Invalid decision: {decision}")

        review.updated_at = datetime.now(timezone.utc)
        result = await self._repository.save(review)
        await self._emit(f"review.{decision}d", review.tenant_id, {
            "review_id": review_id, "decision": decision,
            "decided_by": decided_by, "comments": comments,
        })
        return result

    async def cancel(self, review_id: str) -> Review:
        review = await self._repository.get(review_id)
        if not review:
            raise ValueError(f"Review {review_id} not found")
        if review.is_terminal:
            raise ValueError(f"Cannot cancel review in status: {review.status.value}")
        review.status = ReviewStatus.CANCELLED
        review.updated_at = datetime.now(timezone.utc)
        return await self._repository.save(review)

    async def get(self, review_id: str) -> Review | None:
        return await self._repository.get(review_id)

    async def list_by_target(self, target_id: str) -> list[Review]:
        reviews = await self._repository.list_by_tenant("", target_type=None)
        return [r for r in reviews if r.target_id == target_id]

    async def list_by_tenant(self, tenant_id: str, target_type: str | None = None) -> list[Review]:
        return await self._repository.list_by_tenant(tenant_id, target_type)

    async def list_pending(self, tenant_id: str, assigned_to: str | None = None) -> list[Review]:
        return await self._repository.list_pending(tenant_id, assigned_to)

    async def kpis(self, tenant_id: str) -> dict:
        counts = await self._repository.count_by_status(tenant_id)
        total = sum(counts.values())
        return {
            "total": total,
            "pending": counts.get("pending", 0),
            "in_progress": counts.get("in_progress", 0),
            "approved": counts.get("approved", 0),
            "rejected": counts.get("rejected", 0),
            "escalated": counts.get("escalated", 0),
        }
