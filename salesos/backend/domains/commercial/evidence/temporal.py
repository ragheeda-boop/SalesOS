"""Shared temporal contract for evidence and revenue decisions.

Every producer supplies an observed system-time in UTC.  Optional valid-time
and supersession bounds are checked before a record can be consumed by a
decision or attribution service.  This keeps "what was known when" explicit.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


class TemporalContractError(ValueError):
    pass


@dataclass(frozen=True)
class TemporalEnvelope:
    observed_at: datetime
    valid_from: datetime | None = None
    valid_to: datetime | None = None
    superseded_at: datetime | None = None

    def __post_init__(self) -> None:
        for name, value in (
            ("observed_at", self.observed_at),
            ("valid_from", self.valid_from),
            ("valid_to", self.valid_to),
            ("superseded_at", self.superseded_at),
        ):
            if value is not None and (value.tzinfo is None or value.utcoffset() is None):
                raise TemporalContractError(f"{name} must be timezone-aware")
        if self.observed_at.tzinfo != UTC:
            object.__setattr__(self, "observed_at", self.observed_at.astimezone(UTC))
        if self.valid_from and self.valid_to and self.valid_to < self.valid_from:
            raise TemporalContractError("valid_to cannot precede valid_from")
        if self.superseded_at and self.superseded_at < self.observed_at:
            raise TemporalContractError("superseded_at cannot precede observed_at")

    def as_of(self, at: datetime) -> bool:
        """Whether this observation was current and valid at a UTC instant."""
        point = at if at.tzinfo and at.utcoffset() is not None else at.replace(tzinfo=UTC)
        point = point.astimezone(UTC)
        observed = self.observed_at.astimezone(UTC)
        if point < observed:
            return False
        if self.valid_from and point < self.valid_from.astimezone(UTC):
            return False
        if self.valid_to and point >= self.valid_to.astimezone(UTC):
            return False
        return not self.superseded_at or point < self.superseded_at.astimezone(UTC)

    def freshness(self, *, now: datetime, stale_after: timedelta) -> str:
        point = now if now.tzinfo and now.utcoffset() is not None else now.replace(tzinfo=UTC)
        age = point.astimezone(UTC) - self.observed_at.astimezone(UTC)
        if age < timedelta(0):
            return "FUTURE"
        if age <= stale_after:
            return "FRESH"
        return "STALE"
