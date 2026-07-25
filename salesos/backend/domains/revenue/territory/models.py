from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class Territory:
    """A named sales territory owned by a rep, containing assigned accounts."""

    id: str
    tenant_id: str
    name: str
    region: str = ""
    rep_id: str = ""
    rep_name: str = ""
    account_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def account_count(self) -> int:
        return len(self.account_ids)


@dataclass
class CoverageAnalysis:
    """Per-rep coverage metrics for load analysis."""

    rep_id: str
    rep_name: str = ""
    territory_count: int = 0
    total_accounts: int = 0
    total_pipeline_value: float = 0.0
    accounts_per_territory: float = 0.0
    value_per_account: float = 0.0


@dataclass
class CoverageGap:
    """An account not assigned to any rep."""

    account_id: str
    account_name: str = ""
    pipeline_value: float = 0.0


@dataclass
class LoadBalanceRecommendation:
    """Suggested account move to balance workload."""

    account_id: str
    from_rep_id: str
    to_rep_id: str
    reason: str = ""
    impact_score: float = 0.0


@dataclass
class TerritorySummary:
    """Aggregate territory statistics for a tenant."""

    tenant_id: str
    total_territories: int = 0
    total_accounts: float = 0
    total_reps: int = 0
    unassigned_accounts: int = 0
    avg_accounts_per_rep: float = 0.0
    coverage_gaps: list[CoverageGap] = field(default_factory=list)
    per_rep: list[CoverageAnalysis] = field(default_factory=list)
    recommendations: list[LoadBalanceRecommendation] = field(default_factory=list)
