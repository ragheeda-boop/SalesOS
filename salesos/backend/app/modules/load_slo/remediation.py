"""STORY-14-01 — Documented remediation plan when load SLOs miss."""

from __future__ import annotations

from typing import Any

from app.modules.load_slo.simulator import LoadOutcome
from app.modules.load_slo.targets import ERROR_RATE_MAX, P95_LATENCY_MS_MAX, TARGET_TENANTS


def build_remediation_plan(outcome: LoadOutcome) -> dict[str, Any]:
    """Always return a plan shape; status held|needs_remediation."""
    items: list[str] = []
    if outcome.tenants < TARGET_TENANTS:
        items.append(
            f"Scale simulated concurrency to {TARGET_TENANTS} tenants "
            "(pooled-tier checklist)."
        )
    if outcome.p95_latency_ms > P95_LATENCY_MS_MAX:
        items.append(
            f"p95 latency {outcome.p95_latency_ms:.1f}ms exceeds "
            f"{P95_LATENCY_MS_MAX:.0f}ms — profile hot paths before Sprint 25 gate."
        )
    if outcome.error_rate > ERROR_RATE_MAX:
        items.append(
            f"Error rate {outcome.error_rate:.4f} exceeds {ERROR_RATE_MAX:.2f} — "
            "triage 5xx / timeout budgets."
        )
    if outcome.connection_pool_exhausted:
        items.append(
            "Connection pool exhaustion under 50-tenant load — retune pool size / "
            "checkout timeout (DevOps field)."
        )
    if outcome.degradation_trend:
        items.append(
            "Degradation trend detected — do not silently accept; track remediation "
            "before Sprint 25 gate."
        )
    if not items and outcome.within_slo:
        items.append("SLOs held on CI synthetic profile — field 2h soak remains DevOps residual.")

    status = "held" if outcome.within_slo else "needs_remediation"
    return {
        "status": status,
        "profile": outcome.profile,
        "tenants": outcome.tenants,
        "items": items,
        "reviewed_before_sprint_25_gate": True,
        "honesty": (
            "Documented remediation plan (STORY-14-01). "
            "Not a live prod incident. Not Production GO."
        ),
    }
