"""Pipeline Analytics models — conversion rates, velocity, stage duration, win/loss rates."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass
class ConversionRate:
    """Conversion rate between two pipeline stages."""

    from_stage: str
    to_stage: str
    rate: float = 0.0  # 0.0 - 1.0
    count: int = 0
    total: int = 0


@dataclass
class StageDuration:
    """Average time spent in a specific pipeline stage."""

    stage: str
    avg_days: float = 0.0
    median_days: float = 0.0
    min_days: float = 0.0
    max_days: float = 0.0
    sample_count: int = 0


@dataclass
class VelocityMetrics:
    """Pipeline velocity metrics."""

    avg_cycle_days: float = 0.0
    avg_days_per_stage: dict[str, float] = field(default_factory=dict)
    overall_cycle_time: float = 0.0
    fastest_close_days: float = 0.0
    slowest_close_days: float = 0.0


@dataclass
class PipelineValueOverTime:
    """Monthly pipeline value snapshot."""

    month: str  # e.g. "2026-01"
    total_value: float = 0.0
    weighted_value: float = 0.0
    deal_count: int = 0
    new_deals: int = 0
    closed_deals: int = 0


@dataclass
class WinLossMetrics:
    """Win rate, loss rate, and stagnation rate."""

    win_rate: float = 0.0
    loss_rate: float = 0.0
    stagnation_rate: float = 0.0
    total_won: int = 0
    total_lost: int = 0
    total_stagnant: int = 0
    total_active: int = 0


@dataclass
class PipelineAnalyticsResult:
    """Complete pipeline analytics response."""

    tenant_id: str
    generated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    # Conversion
    conversion_rates: list[ConversionRate] = field(default_factory=list)
    overall_conversion_rate: float = 0.0

    # Velocity
    velocity: VelocityMetrics = field(default_factory=VelocityMetrics)

    # Stage durations
    stage_durations: list[StageDuration] = field(default_factory=list)

    # Pipeline value over time
    value_over_time: list[PipelineValueOverTime] = field(default_factory=list)

    # Win/Loss
    win_loss: WinLossMetrics = field(default_factory=WinLossMetrics)

    # Summary
    total_pipeline_value: float = 0.0
    total_weighted_value: float = 0.0
    active_deals: int = 0

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "generated_at": self.generated_at.isoformat(),
            "conversion_rates": [
                {"from": c.from_stage, "to": c.to_stage, "rate": c.rate, "count": c.count, "total": c.total}
                for c in self.conversion_rates
            ],
            "overall_conversion_rate": self.overall_conversion_rate,
            "velocity": {
                "avg_cycle_days": self.velocity.avg_cycle_days,
                "avg_days_per_stage": self.velocity.avg_days_per_stage,
                "fastest_close_days": self.velocity.fastest_close_days,
                "slowest_close_days": self.velocity.slowest_close_days,
            },
            "stage_durations": [
                {"stage": s.stage, "avg_days": s.avg_days, "median_days": s.median_days,
                 "min_days": s.min_days, "max_days": s.max_days, "sample_count": s.sample_count}
                for s in self.stage_durations
            ],
            "value_over_time": [
                {"month": v.month, "total_value": v.total_value, "weighted_value": v.weighted_value,
                 "deal_count": v.deal_count, "new_deals": v.new_deals, "closed_deals": v.closed_deals}
                for v in self.value_over_time
            ],
            "win_loss": {
                "win_rate": self.win_loss.win_rate,
                "loss_rate": self.win_loss.loss_rate,
                "stagnation_rate": self.win_loss.stagnation_rate,
                "total_won": self.win_loss.total_won,
                "total_lost": self.win_loss.total_lost,
                "total_stagnant": self.win_loss.total_stagnant,
                "total_active": self.win_loss.total_active,
            },
            "total_pipeline_value": self.total_pipeline_value,
            "total_weighted_value": self.total_weighted_value,
            "active_deals": self.active_deals,
        }
