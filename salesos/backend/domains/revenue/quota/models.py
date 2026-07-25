from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class QuotaPeriod(Enum):
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"


class QuotaStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    EXPIRED = "expired"


@dataclass
class Quota:
    """A revenue target assigned to a rep for a time period."""

    id: str
    tenant_id: str
    rep_id: str
    rep_name: str = ""
    period: QuotaPeriod = QuotaPeriod.QUARTERLY
    target_amount: float = 0.0
    attained_amount: float = 0.0
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    status: QuotaStatus = QuotaStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def attainment_percent(self) -> float:
        if self.target_amount <= 0:
            return 0.0
        return round((self.attained_amount / self.target_amount) * 100, 2)

    @property
    def remaining_amount(self) -> float:
        return max(self.target_amount - self.attained_amount, 0.0)

    @property
    def is_on_track(self) -> bool:
        now = datetime.now(timezone.utc)
        if self.end_date <= self.start_date:
            return False
        elapsed_ratio = min(
            (now - self.start_date).total_seconds()
            / (self.end_date - self.start_date).total_seconds(),
            1.0,
        )
        return self.attainment_percent >= (elapsed_ratio * 100)


@dataclass
class QuotaForecast:
    """Forecast attainment based on current velocity."""

    quota_id: str
    rep_id: str
    current_velocity: float = 0.0          # revenue per day
    days_remaining: float = 0.0
    projected_attainment: float = 0.0      # attained + (velocity × remaining_days)
    projected_attainment_percent: float = 0.0
    will_hit_target: bool = False
    confidence: float = 0.0


@dataclass
class TeamAggregate:
    """Aggregate quota stats for a team."""

    tenant_id: str
    total_targets: float = 0.0
    total_attained: float = 0.0
    overall_attainment_percent: float = 0.0
    rep_count: int = 0
    reps_on_track: int = 0
    reps_at_risk: int = 0
    reps_missed: int = 0


@dataclass
class QuotaSnapshot:
    """Immutable snapshot of all quotas at a point in time."""

    id: str
    tenant_id: str
    period_label: str = ""
    quotas: list[Quota] = field(default_factory=list)
    team: TeamAggregate | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_target(self) -> float:
        return sum(q.target_amount for q in self.quotas)

    @property
    def total_attained(self) -> float:
        return sum(q.attained_amount for q in self.quotas)

    @property
    def overall_attainment(self) -> float:
        if self.total_target <= 0:
            return 0.0
        return round((self.total_attained / self.total_target) * 100, 2)
