"""Copilot feedback service — in-memory store for feedback records.

Provides submission, retrieval, and aggregated statistics.
Will be swapped for PostgreSQL repository in production.
"""

from __future__ import annotations

import logging
from collections import defaultdict

from domains.copilot.models import (
    CopilotFeedback,
    CopilotFeedbackStats,
    FeedbackRating,
)

logger = logging.getLogger(__name__)


class CopilotFeedbackService:
    """In-memory feedback service for copilot responses."""

    def __init__(self) -> None:
        self._records: list[CopilotFeedback] = []

    def submit(
        self,
        *,
        conversation_id: str,
        message_id: str,
        user_id: str,
        tenant_id: str,
        rating: str,
        comment: str = "",
        tool_name: str | None = None,
    ) -> CopilotFeedback:
        feedback = CopilotFeedback(
            conversation_id=conversation_id,
            message_id=message_id,
            user_id=user_id,
            tenant_id=tenant_id,
            rating=FeedbackRating(rating),
            comment=comment,
            tool_name=tool_name,
        )
        self._records.append(feedback)
        logger.info(
            "Copilot feedback: id=%s rating=%s tool=%s",
            feedback.id,
            feedback.rating.value,
            feedback.tool_name,
        )
        return feedback

    def get_stats(self, tenant_id: str | None = None) -> CopilotFeedbackStats:
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]

        total = len(records)
        positive = sum(1 for r in records if r.rating == FeedbackRating.UP)
        negative = sum(1 for r in records if r.rating == FeedbackRating.DOWN)
        satisfaction = positive / total if total > 0 else 0.0

        by_tool: dict[str, dict[str, int]] = defaultdict(
            lambda: {"positive": 0, "negative": 0, "total": 0}
        )
        for r in records:
            tool = r.tool_name or "general"
            by_tool[tool]["total"] += 1
            if r.rating == FeedbackRating.UP:
                by_tool[tool]["positive"] += 1
            else:
                by_tool[tool]["negative"] += 1

        return CopilotFeedbackStats(
            total_feedback=total,
            positive_count=positive,
            negative_count=negative,
            satisfaction_rate=round(satisfaction, 4),
            by_tool=dict(by_tool),
        )

    def list_feedback(
        self,
        tenant_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CopilotFeedback]:
        records = self._records
        if tenant_id:
            records = [r for r in records if r.tenant_id == tenant_id]
        return records[offset: offset + limit]

    def count(self, tenant_id: str | None = None) -> int:
        if tenant_id:
            return sum(1 for r in self._records if r.tenant_id == tenant_id)
        return len(self._records)
