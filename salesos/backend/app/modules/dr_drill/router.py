"""STORY-14-03 — DR drill HTTP (auth-gated).

Not Production GO. No live prod restore. feature_ai_copilot False.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import verify_token
from app.modules.dr_drill.harness import DEFAULT_DR_HARNESS, MemDrDrillHarness
from app.modules.dr_drill.targets import (
    DRILL_KINDS,
    RPO_TARGET_SECONDS,
    RTO_TARGET_SECONDS,
)

router = APIRouter(prefix="/dr", tags=["DR Drill"])
_AUTH = [Depends(verify_token)]

_HARNESS = DEFAULT_DR_HARNESS


class DrillResponse(BaseModel):
    id: str
    drill_kind: str
    ok: bool
    within_rto: bool
    within_rpo: bool
    rto_seconds: float
    rpo_seconds: float
    restore: dict[str, Any] = Field(default_factory=dict)
    postmortem: dict[str, Any] = Field(default_factory=dict)
    ran_at: str = ""
    honesty: str = ""


class PostmortemResponse(BaseModel):
    drill_id: str
    drill_kind: str
    outcome: str
    summary: str
    rto_seconds: float = 0.0
    rpo_seconds: float = 0.0
    within_rto: bool = False
    within_rpo: bool = False
    what_went_well: list[str] = Field(default_factory=list)
    what_to_improve: list[str] = Field(default_factory=list)
    residuals: list[str] = Field(default_factory=list)
    written_at: str = ""
    honesty: str = ""


@router.get("/meta", dependencies=_AUTH)
async def dr_meta() -> dict[str, Any]:
    return {
        "story": "STORY-14-03",
        "drill_kinds": sorted(DRILL_KINDS),
        "rto_target_seconds": RTO_TARGET_SECONDS,
        "rpo_target_seconds": RPO_TARGET_SECONDS,
        "persistence": "memory",
        "policy_count_delta": 0,
        "feature_ai_copilot": settings.feature_ai_copilot,
        "stage6_ghcr": "quarantined",
        "honesty": (
            "CI/non-prod DR harness (backup/restore + PITR). "
            "Live production restore and Production GO not claimed."
        ),
    }


@router.post("/run/{drill_kind}", response_model=DrillResponse, dependencies=_AUTH)
async def run_dr_drill(drill_kind: str) -> DrillResponse:
    try:
        report = _HARNESS.run(drill_kind)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return DrillResponse.model_validate(report.as_dict())


@router.post("/run-all", response_model=list[DrillResponse], dependencies=_AUTH)
async def run_all_dr_drills() -> list[DrillResponse]:
    return [DrillResponse.model_validate(r.as_dict()) for r in _HARNESS.run_all()]


@router.get("/drills", response_model=list[DrillResponse], dependencies=_AUTH)
async def list_dr_drills() -> list[DrillResponse]:
    return [DrillResponse.model_validate(r.as_dict()) for r in _HARNESS.list_drills()]


@router.get("/drills/{drill_id}", response_model=DrillResponse, dependencies=_AUTH)
async def get_dr_drill(drill_id: str) -> DrillResponse:
    row = _HARNESS.get_drill(drill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="dr drill not found")
    return DrillResponse.model_validate(row.as_dict())


@router.get("/postmortems", response_model=list[PostmortemResponse], dependencies=_AUTH)
async def list_dr_postmortems() -> list[PostmortemResponse]:
    return [PostmortemResponse.model_validate(p.as_dict()) for p in _HARNESS.list_postmortems()]


def bind_harness(harness: MemDrDrillHarness) -> None:
    global _HARNESS  # noqa: PLW0603
    _HARNESS = harness
