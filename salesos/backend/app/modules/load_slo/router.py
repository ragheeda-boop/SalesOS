"""STORY-14-01 — Load/SLO harness HTTP (auth-gated).

Not Production GO. No live prod kill. feature_ai_copilot False.
Companion tip HTTP for DevOps 50-tenant field harness.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import verify_token
from app.modules.load_slo.harness import DEFAULT_LOAD_SLO_HARNESS, MemLoadSloHarness
from app.modules.load_slo.targets import (
    ERROR_RATE_MAX,
    LOAD_PROFILES,
    P95_LATENCY_MS_MAX,
    TARGET_TENANTS,
)

router = APIRouter(prefix="/load", tags=["Load SLO"])
_AUTH = [Depends(verify_token)]

_HARNESS = DEFAULT_LOAD_SLO_HARNESS


class RunResponse(BaseModel):
    id: str
    profile: str
    ok: bool
    within_slo: bool
    tenants: int
    p95_latency_ms: float
    error_rate: float
    connection_pool_exhausted: bool
    degradation_trend: bool
    metrics: dict[str, Any] = Field(default_factory=dict)
    remediation: dict[str, Any] = Field(default_factory=dict)
    postmortem: dict[str, Any] = Field(default_factory=dict)
    ran_at: str = ""
    honesty: str = ""


class PostmortemResponse(BaseModel):
    run_id: str
    profile: str
    outcome: str
    summary: str
    tenants: int = 0
    p95_latency_ms: float = 0.0
    error_rate: float = 0.0
    within_slo: bool = False
    what_went_well: list[str] = Field(default_factory=list)
    what_to_improve: list[str] = Field(default_factory=list)
    residuals: list[str] = Field(default_factory=list)
    written_at: str = ""
    honesty: str = ""


@router.get("/meta", dependencies=_AUTH)
async def load_meta() -> dict[str, Any]:
    return {
        "story": "STORY-14-01",
        "target_tenants": TARGET_TENANTS,
        "profiles": sorted(LOAD_PROFILES),
        "slo": {
            "p95_latency_ms_max": P95_LATENCY_MS_MAX,
            "error_rate_max": ERROR_RATE_MAX,
            "connection_pool_exhaustion": "must_be_false",
            "degradation_trend": "must_be_false",
        },
        "persistence": "memory",
        "policy_count_delta": 0,
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "stage6_ghcr": "quarantined",
        "honesty": (
            "CI/non-prod load/SLO harness companion (50-tenant pooled tier). "
            "Field 2h soak + live prod traffic/kill and Production GO not claimed."
        ),
    }


@router.post("/run/{profile}", response_model=RunResponse, dependencies=_AUTH)
async def run_load_profile(profile: str) -> RunResponse:
    try:
        report = _HARNESS.run(profile)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RunResponse.model_validate(report.as_dict())


@router.post("/run-all", response_model=list[RunResponse], dependencies=_AUTH)
async def run_all_load_profiles() -> list[RunResponse]:
    return [RunResponse.model_validate(r.as_dict()) for r in _HARNESS.run_all()]


@router.get("/runs", response_model=list[RunResponse], dependencies=_AUTH)
async def list_load_runs() -> list[RunResponse]:
    return [RunResponse.model_validate(r.as_dict()) for r in _HARNESS.list_runs()]


@router.get("/runs/{run_id}", response_model=RunResponse, dependencies=_AUTH)
async def get_load_run(run_id: str) -> RunResponse:
    row = _HARNESS.get_run(run_id)
    if row is None:
        raise HTTPException(status_code=404, detail="load run not found")
    return RunResponse.model_validate(row.as_dict())


@router.get("/remediation", dependencies=_AUTH)
async def get_latest_remediation() -> dict[str, Any]:
    latest = _HARNESS.latest_remediation()
    if not latest:
        return {
            "status": "none",
            "items": [],
            "honesty": "No load run yet — remediation empty.",
        }
    return latest


@router.get("/postmortems", response_model=list[PostmortemResponse], dependencies=_AUTH)
async def list_load_postmortems() -> list[PostmortemResponse]:
    return [PostmortemResponse.model_validate(p.as_dict()) for p in _HARNESS.list_postmortems()]


def bind_harness(harness: MemLoadSloHarness) -> None:
    global _HARNESS  # noqa: PLW0603
    _HARNESS = harness
