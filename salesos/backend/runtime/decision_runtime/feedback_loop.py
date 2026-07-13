"""Decision Feedback Loop — tracks decision lifecycle and learning for future AI training.

Every decision goes through:
  Decision → User Accepted/Rejected → Executed/Ignored → Outcome (Won/Lost) → Learning

This data becomes the foundation for future ML/AI models.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from typing import Any, Optional

from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)

_DEFAULT_MAX_ENTRIES = 10000
_DEFAULT_ENTRY_TTL_SECONDS = 3600


class FeedbackOutcome(str, Enum):
    WON = "won"
    LOST = "lost"
    PENDING = "pending"
    NO_MEETING = "no_meeting"
    IGNORED = "ignored"
    CANCELLED = "cancelled"


@dataclass
class FeedbackLoopEntry:
    decision_id: str
    company_id: str
    tenant_id: str
    user_accepted: bool
    executed: bool
    outcome: Optional[FeedbackOutcome] = None
    outcome_value: Optional[float] = None
    learning: Optional[str] = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict:
        return {
            "decision_id": self.decision_id,
            "company_id": self.company_id,
            "tenant_id": self.tenant_id,
            "user_accepted": self.user_accepted,
            "executed": self.executed,
            "outcome": self.outcome.value if self.outcome else None,
            "outcome_value": self.outcome_value,
            "learning": self.learning,
            "created_at": self.created_at.isoformat(),
        }


class DecisionFeedbackLoop:
    """Tracks decision lifecycle for learning.

    Flow:
      1. Decision suggested
      2. User accepts or rejects
      3. If accepted → executed or ignored
      4. If executed → outcome (won/lost/no_meeting)
      5. Learning extracted for future model training
    """

    def __init__(self, session_factory, logger=None):
        self._session_factory = session_factory
        self._logger = logger
        self._entries: list[FeedbackLoopEntry] = []
        self._max_entries = _DEFAULT_MAX_ENTRIES
        self._entry_ttl = _DEFAULT_ENTRY_TTL_SECONDS

    async def record_feedback(
        self,
        decision_id: str,
        company_id: str,
        tenant_id: str,
        accepted: bool,
        executed: bool = False,
        outcome: Optional[str] = None,
        outcome_value: Optional[float] = None,
        learning: Optional[str] = None,
    ) -> FeedbackLoopEntry:
        entry = FeedbackLoopEntry(
            decision_id=decision_id,
            company_id=company_id,
            tenant_id=tenant_id,
            user_accepted=accepted,
            executed=executed,
            outcome=FeedbackOutcome(outcome) if outcome else None,
            outcome_value=outcome_value,
            learning=learning,
        )
        self._evict_entries()
        self._entries.append(entry)

        async with self._session_factory() as session:
            await session.execute(
                sa_text("""
                    INSERT INTO decision_feedback_loop
                        (decision_id, company_id, tenant_id, user_accepted, executed,
                         outcome, outcome_value, learning, created_at)
                    VALUES (:did, :cid, :tid, :ua, :ex, :out, :ov, :learn, :ca)
                """),
                {
                    "did": decision_id,
                    "cid": company_id,
                    "tid": tenant_id,
                    "ua": accepted,
                    "ex": executed,
                    "out": outcome,
                    "ov": outcome_value,
                    "learn": learning,
                    "ca": entry.created_at,
                },
            )
            await session.commit()

        return entry

    def get_feedback(self, decision_id: str) -> Optional[FeedbackLoopEntry]:
        for e in reversed(self._entries):
            if e.decision_id == decision_id:
                return e
        return None

    def get_all_feedback(self, company_id: str) -> list[dict]:
        return [e.to_dict() for e in self._entries if e.company_id == company_id]

    def learning_summary(self) -> dict:
        """Aggregate learning for future AI training."""
        total = len(self._entries)
        won = sum(1 for e in self._entries if e.outcome == FeedbackOutcome.WON)
        lost = sum(1 for e in self._entries if e.outcome == FeedbackOutcome.LOST)
        ignored = sum(1 for e in self._entries if e.outcome == FeedbackOutcome.IGNORED)
        return {
            "total_decisions": total,
            "won": won,
            "lost": lost,
            "ignored": ignored,
            "win_rate": round(won / max(total, 1), 2),
            "outcome_value_total": sum(e.outcome_value or 0 for e in self._entries),
        }

    def _evict_entries(self) -> int:
        """Evict expired and overflow entries. Returns number evicted."""
        evicted = 0
        now = datetime.now(timezone.utc)
        cutoff = now - timedelta(seconds=self._entry_ttl)

        kept = []
        for e in self._entries:
            if e.created_at and e.created_at >= cutoff:
                kept.append(e)
            else:
                evicted += 1

        overflow = len(kept) - self._max_entries
        if overflow > 0:
            kept = kept[overflow:]
            evicted += overflow

        self._entries = kept

        if evicted > 0 and self._logger:
            self._logger.warning(
                "Feedback loop evicted %d entries (current=%d, max=%d, ttl=%ds)",
                evicted, len(self._entries), self._max_entries, self._entry_ttl,
            )

        return evicted
