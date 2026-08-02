"""STORY-14-06 — AI provider failover HTTP (non-prod), nested under /chaos.

Auth-gated. feature_ai_copilot False. No live LLM. Not Production GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import verify_token
from app.modules.chaos_resilience.ai_failover import VALID_AI_FAILOVER_SCENARIOS
from app.modules.chaos_resilience.ai_failover_harness import (
    DEFAULT_AI_FAILOVER_HARNESS,
    MemAiFailoverHarness,
)
from app.modules.chaos_resilience.faults import AI_FAILOVER_SLO_SECONDS

router = APIRouter(prefix="/chaos/ai-failover", tags=["Chaos Resilience"])
_AUTH = [Depends(verify_token)]

_HARNESS = DEFAULT_AI_FAILOVER_HARNESS


class AiFailoverDrillResponse(BaseModel):
    id: str
    scenario: str
    ok: bool
    graceful: bool
    within_slo: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
    postmortem: dict[str, Any] = Field(default_factory=dict)
    ran_at: str = ""
    honesty: str = ""


class AiFailoverPostmortemResponse(BaseModel):
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
async def ai_failover_meta() -> dict[str, Any]:
    meta = _HARNESS.meta()
    meta["feature_ai_copilot"] = bool(settings.feature_ai_copilot)
    meta["slo_seconds"] = AI_FAILOVER_SLO_SECONDS
    return meta


@router.get("/scenarios", dependencies=_AUTH)
async def list_scenarios() -> dict[str, Any]:
    return {
        "scenarios": sorted(VALID_AI_FAILOVER_SCENARIOS),
        "slo_seconds": AI_FAILOVER_SLO_SECONDS,
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
    }


@router.post("/run/{scenario}", response_model=AiFailoverDrillResponse, dependencies=_AUTH)
async def run_ai_failover(scenario: str) -> AiFailoverDrillResponse:
    try:
        report = _HARNESS.run(scenario)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AiFailoverDrillResponse.model_validate(report.as_dict())


@router.post("/run-all", response_model=list[AiFailoverDrillResponse], dependencies=_AUTH)
async def run_all_ai_failover() -> list[AiFailoverDrillResponse]:
    return [AiFailoverDrillResponse.model_validate(r.as_dict()) for r in _HARNESS.run_all()]


@router.get("/drills", response_model=list[AiFailoverDrillResponse], dependencies=_AUTH)
async def list_ai_failover_drills() -> list[AiFailoverDrillResponse]:
    return [AiFailoverDrillResponse.model_validate(r.as_dict()) for r in _HARNESS.list_drills()]


@router.get("/drills/{drill_id}", response_model=AiFailoverDrillResponse, dependencies=_AUTH)
async def get_ai_failover_drill(drill_id: str) -> AiFailoverDrillResponse:
    row = _HARNESS.get_drill(drill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="ai failover drill not found")
    return AiFailoverDrillResponse.model_validate(row.as_dict())


@router.get("/postmortems", response_model=list[AiFailoverPostmortemResponse], dependencies=_AUTH)
async def list_ai_failover_postmortems() -> list[AiFailoverPostmortemResponse]:
    rows = _HARNESS.list_postmortems()
    return [AiFailoverPostmortemResponse.model_validate(p.as_dict()) for p in rows]


def bind_harness(harness: MemAiFailoverHarness) -> None:
    global _HARNESS  # noqa: PLW0603
    _HARNESS = harness
