"""In-memory Review repository for testing."""

from __future__ import annotations

from ..contracts.models import Review
from ..contracts.repository import ReviewRepository


class InMemoryReviewRepository(ReviewRepository):

    def __init__(self):
        self._reviews: dict[str, Review] = {}

    async def save(self, review: Review) -> Review:
        self._reviews[review.id] = review
        return review

    async def get(self, review_id: str) -> Review | None:
        return self._reviews.get(review_id)

    async def list_by_tenant(self, tenant_id: str, target_type: str | None = None) -> list[Review]:
        results = [r for r in self._reviews.values() if r.tenant_id == tenant_id]
        if target_type:
            results = [r for r in results if r.target_type == target_type]
        return results

    async def list_pending(self, tenant_id: str, assigned_to: str | None = None) -> list[Review]:
        results = [r for r in self._reviews.values()
                   if r.tenant_id == tenant_id and r.status.value == "pending"]
        if assigned_to:
            results = [r for r in results if r.assigned_to == assigned_to]
        return results

    async def count_by_status(self, tenant_id: str) -> dict[str, int]:
        counts: dict[str, int] = {}
        for r in self._reviews.values():
            if r.tenant_id == tenant_id:
                counts[r.status.value] = counts.get(r.status.value, 0) + 1
        return counts
