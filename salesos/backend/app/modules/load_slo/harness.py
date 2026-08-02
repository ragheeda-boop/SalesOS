"""STORY-14-01 — Load/SLO harness (50-tenant pooled tier companion).

CI/non-prod only. Not Production GO. DEC-085 untouched. No FORCE RLS.
Pairs with DevOps field load harness — BE tip HTTP support.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any

from app.modules.load_slo.postmortem import (
    PracticePostmortem,
    write_load_postmortem,
)
from app.modules.load_slo.remediation import build_remediation_plan
from app.modules.load_slo.simulator import (
    LoadOutcome,
    run_pooled_50_tenant_burst,
    run_pooled_50_tenant_sustained_sim,
)
from app.modules.load_slo.targets import LOAD_PROFILES


@dataclass
class LoadRunReport:
    id: str
    profile: str
    ok: bool
    within_slo: bool
    tenants: int
    p95_latency_ms: float
    error_rate: float
    connection_pool_exhausted: bool
    degradation_trend: bool
    metrics: dict[str, Any] = field(default_factory=dict)
    remediation: dict[str, Any] = field(default_factory=dict)
    postmortem: dict[str, Any] = field(default_factory=dict)
    ran_at: str = ""
    honesty: str = (
        "CI/non-prod load/SLO harness companion only; live prod traffic/kill "
        "not performed. Not Production GO. feature_ai_copilot=False."
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "profile": self.profile,
            "ok": self.ok,
            "within_slo": self.within_slo,
            "tenants": self.tenants,
            "p95_latency_ms": self.p95_latency_ms,
            "error_rate": self.error_rate,
            "connection_pool_exhausted": self.connection_pool_exhausted,
            "degradation_trend": self.degradation_trend,
            "metrics": dict(self.metrics),
            "remediation": dict(self.remediation),
            "postmortem": dict(self.postmortem),
            "ran_at": self.ran_at,
            "honesty": self.honesty,
        }


@dataclass
class MemLoadSloHarness:
    _runs: dict[str, LoadRunReport] = field(default_factory=dict)
    _postmortems: dict[str, PracticePostmortem] = field(default_factory=dict)
    _remediation_latest: dict[str, Any] = field(default_factory=dict)

    def run(self, profile: str) -> LoadRunReport:
        kind = (profile or "").strip().lower()
        if kind not in LOAD_PROFILES:
            raise ValueError(
                f"unknown profile={profile!r}; expected one of {sorted(LOAD_PROFILES)}"
            )
        outcome = self._dispatch(kind)
        run_id = uuid.uuid4().hex[:12]
        remediation = build_remediation_plan(outcome)
        pm = write_load_postmortem(
            run_id=run_id,
            profile=kind,
            ok=outcome.ok,
            tenants=outcome.tenants,
            p95_latency_ms=outcome.p95_latency_ms,
            error_rate=outcome.error_rate,
            within_slo=outcome.within_slo,
            remediation_items=list(remediation.get("items") or []),
        )
        report = LoadRunReport(
            id=run_id,
            profile=kind,
            ok=outcome.ok,
            within_slo=outcome.within_slo,
            tenants=outcome.tenants,
            p95_latency_ms=outcome.p95_latency_ms,
            error_rate=outcome.error_rate,
            connection_pool_exhausted=outcome.connection_pool_exhausted,
            degradation_trend=outcome.degradation_trend,
            metrics=outcome.as_dict(),
            remediation=remediation,
            postmortem=pm.as_dict(),
            ran_at=datetime.now(UTC).isoformat(),
        )
        self._runs[run_id] = report
        self._postmortems[run_id] = pm
        self._remediation_latest = remediation
        return report

    def _dispatch(self, kind: str) -> LoadOutcome:
        if kind == "pooled_50_tenant_burst":
            return run_pooled_50_tenant_burst()
        if kind == "pooled_50_tenant_sustained_sim":
            return run_pooled_50_tenant_sustained_sim()
        raise ValueError(f"unhandled profile={kind}")

    def list_runs(self) -> list[LoadRunReport]:
        return sorted(self._runs.values(), key=lambda r: r.ran_at)

    def get_run(self, run_id: str) -> LoadRunReport | None:
        return self._runs.get(str(run_id))

    def list_postmortems(self) -> list[PracticePostmortem]:
        return sorted(self._postmortems.values(), key=lambda p: p.written_at)

    def latest_remediation(self) -> dict[str, Any]:
        return dict(self._remediation_latest)

    def run_all(self) -> list[LoadRunReport]:
        return [self.run(k) for k in sorted(LOAD_PROFILES)]


DEFAULT_LOAD_SLO_HARNESS = MemLoadSloHarness()
