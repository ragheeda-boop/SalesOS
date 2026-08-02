"""STORY-14-02 — Chaos resilience HTTP (auth-gated).

Not Production GO. No live ERP/DB kill. feature_ai_copilot False.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import verify_token
from app.modules.chaos_resilience.faults import (
    AI_FAILOVER_SLO_SECONDS,
    VALID_FAULT_KINDS,
)
from app.modules.chaos_resilience.harness import (
    DEFAULT_CHAOS_HARNESS,
    MemChaosHarness,
)

router = APIRouter(prefix="/chaos", tags=["Chaos Resilience"])
_AUTH = [Depends(verify_token)]

_HARNESS = DEFAULT_CHAOS_HARNESS


class DrillResponse(BaseModel):
    id: str
    fault_kind: str
    ok: bool
    graceful: bool
    handler: dict[str, Any] = Field(default_factory=dict)
    postmortem: dict[str, Any] = Field(default_factory=dict)
    ran_at: str = ""
    honesty: str = ""


class PostmortemResponse(BaseModel):
    drill_id: str
    fault_kind: str
    outcome: str
    summary: str
    what_went_well: list[str] = Field(default_factory=list)
    what_to_improve: list[str] = Field(default_factory=list)
    residuals: list[str] = Field(default_factory=list)
    written_at: str = ""
    honesty: str = ""


@router.get("/meta", dependencies=_AUTH)
async def chaos_meta() -> dict[str, Any]:
    return {
        "story": "STORY-14-02",
        "fault_kinds": sorted(VALID_FAULT_KINDS),
        "ai_failover_slo_seconds": AI_FAILOVER_SLO_SECONDS,
        "persistence": "memory",
        "policy_count_delta": 0,
        "feature_ai_copilot": False,
        "stage6_ghcr": "quarantined",
        "honesty": (
            "CI fault-injection harness (connector/AI/DB). "
            "Live kills and Production GO not claimed."
        ),
    }


@router.post("/run/{fault_kind}", response_model=DrillResponse, dependencies=_AUTH)
async def run_chaos_drill(fault_kind: str) -> DrillResponse:
    try:
        report = _HARNESS.run(fault_kind)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DrillResponse.model_validate(report.as_dict())


@router.post("/run-all", response_model=list[DrillResponse], dependencies=_AUTH)
async def run_all_chaos_drills() -> list[DrillResponse]:
    reports = _HARNESS.run_all()
    return [DrillResponse.model_validate(r.as_dict()) for r in reports]


@router.get("/drills", response_model=list[DrillResponse], dependencies=_AUTH)
async def list_chaos_drills() -> list[DrillResponse]:
    return [DrillResponse.model_validate(r.as_dict()) for r in _HARNESS.list_drills()]


@router.get("/drills/{drill_id}", response_model=DrillResponse, dependencies=_AUTH)
async def get_chaos_drill(drill_id: str) -> DrillResponse:
    row = _HARNESS.get_drill(drill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="chaos drill not found")
    return DrillResponse.model_validate(row.as_dict())


@router.get("/postmortems", response_model=list[PostmortemResponse], dependencies=_AUTH)
async def list_practice_postmortems() -> list[PostmortemResponse]:
    rows = _HARNESS.list_postmortems()
    return [PostmortemResponse.model_validate(p.as_dict()) for p in rows]


def bind_harness(harness: MemChaosHarness) -> None:
    global _HARNESS  # noqa: PLW0603
    _HARNESS = harness
