"""STORY-14-01 — Simulated 50-tenant load outcomes (CI/non-prod).

Not a live k6/locust run. DevOps owns field harness; BE exposes measurable
SLO shape + remediation plan. Not Production GO.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.modules.load_slo.targets import (
    ERROR_RATE_MAX,
    P95_LATENCY_MS_MAX,
    TARGET_TENANTS,
)


@dataclass
class LoadOutcome:
    ok: bool
    profile: str
    tenants: int
    p95_latency_ms: float
    error_rate: float
    connection_pool_exhausted: bool
    degradation_trend: bool
    within_slo: bool
    detail: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "profile": self.profile,
            "tenants": self.tenants,
            "p95_latency_ms": self.p95_latency_ms,
            "error_rate": self.error_rate,
            "connection_pool_exhausted": self.connection_pool_exhausted,
            "degradation_trend": self.degradation_trend,
            "within_slo": self.within_slo,
            "detail": dict(self.detail),
        }


def _evaluate(
    *,
    profile: str,
    tenants: int,
    p95_latency_ms: float,
    error_rate: float,
    connection_pool_exhausted: bool,
    degradation_trend: bool,
    detail: dict[str, Any],
) -> LoadOutcome:
    within = (
        tenants >= TARGET_TENANTS
        and p95_latency_ms <= P95_LATENCY_MS_MAX
        and error_rate <= ERROR_RATE_MAX
        and not connection_pool_exhausted
        and not degradation_trend
    )
    return LoadOutcome(
        ok=within,
        profile=profile,
        tenants=tenants,
        p95_latency_ms=p95_latency_ms,
        error_rate=error_rate,
        connection_pool_exhausted=connection_pool_exhausted,
        degradation_trend=degradation_trend,
        within_slo=within,
        detail=detail,
    )


def run_pooled_50_tenant_burst(
    *,
    tenants: int = TARGET_TENANTS,
    p95_latency_ms: float = 180.0,
    error_rate: float = 0.002,
    connection_pool_exhausted: bool = False,
    degradation_trend: bool = False,
) -> LoadOutcome:
    return _evaluate(
        profile="pooled_50_tenant_burst",
        tenants=tenants,
        p95_latency_ms=p95_latency_ms,
        error_rate=error_rate,
        connection_pool_exhausted=connection_pool_exhausted,
        degradation_trend=degradation_trend,
        detail={
            "mode": "ci_synthetic_burst",
            "target": "nonprod_load_fixture",
            "concurrent_tenants": tenants,
            "live_traffic": False,
            "prod_kill": False,
        },
    )


def run_pooled_50_tenant_sustained_sim(
    *,
    tenants: int = TARGET_TENANTS,
    p95_latency_ms: float = 220.0,
    error_rate: float = 0.004,
    connection_pool_exhausted: bool = False,
    degradation_trend: bool = False,
    simulated_duration_seconds: float = 120.0,
) -> LoadOutcome:
    """Compressed sustained profile for CI — not a 2h field soak."""
    return _evaluate(
        profile="pooled_50_tenant_sustained_sim",
        tenants=tenants,
        p95_latency_ms=p95_latency_ms,
        error_rate=error_rate,
        connection_pool_exhausted=connection_pool_exhausted,
        degradation_trend=degradation_trend,
        detail={
            "mode": "ci_synthetic_sustained_sim",
            "target": "nonprod_load_fixture",
            "concurrent_tenants": tenants,
            "simulated_duration_seconds": simulated_duration_seconds,
            "field_2h_soak": False,
            "live_traffic": False,
            "prod_kill": False,
        },
    )
