"""STORY-14-07 — LLM regression HTTP (non-prod), nested under /chaos.

Auth-gated. feature_ai_copilot False. No live LLM. Not Production GO.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.config import settings
from app.dependencies import verify_token
from app.modules.chaos_resilience.llm_regression import (
    SIMILARITY_THRESHOLD,
    VALID_LLM_REGRESSION_MODES,
)
from app.modules.chaos_resilience.llm_regression_harness import (
    DEFAULT_LLM_REGRESSION_HARNESS,
    MemLlmRegressionHarness,
)

router = APIRouter(prefix="/chaos/llm-regression", tags=["Chaos Resilience"])
_AUTH = [Depends(verify_token)]

_HARNESS = DEFAULT_LLM_REGRESSION_HARNESS


class LlmRegressionDrillResponse(BaseModel):
    id: str
    mode: str
    ok: bool
    baseline_established: bool = False
    regression_detected: bool = False
    promotion_blocked: bool = False
    result: dict[str, Any] = Field(default_factory=dict)
    postmortem: dict[str, Any] = Field(default_factory=dict)
    ran_at: str = ""
    honesty: str = ""


class LlmRegressionPostmortemResponse(BaseModel):
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
async def llm_regression_meta() -> dict[str, Any]:
    meta = _HARNESS.meta()
    meta["feature_ai_copilot"] = bool(settings.feature_ai_copilot)
    meta["similarity_threshold"] = SIMILARITY_THRESHOLD
    return meta


@router.get("/modes", dependencies=_AUTH)
async def list_modes() -> dict[str, Any]:
    return {
        "modes": sorted(VALID_LLM_REGRESSION_MODES),
        "similarity_threshold": SIMILARITY_THRESHOLD,
        "feature_ai_copilot": bool(settings.feature_ai_copilot),
        "live_llm": False,
    }


@router.post("/run/{mode}", response_model=LlmRegressionDrillResponse, dependencies=_AUTH)
async def run_llm_regression_mode(mode: str) -> LlmRegressionDrillResponse:
    try:
        report = _HARNESS.run(mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return LlmRegressionDrillResponse.model_validate(report.as_dict())


@router.post("/run-all", response_model=list[LlmRegressionDrillResponse], dependencies=_AUTH)
async def run_all_llm_regression() -> list[LlmRegressionDrillResponse]:
    return [LlmRegressionDrillResponse.model_validate(r.as_dict()) for r in _HARNESS.run_all()]


@router.get("/drills", response_model=list[LlmRegressionDrillResponse], dependencies=_AUTH)
async def list_llm_regression_drills() -> list[LlmRegressionDrillResponse]:
    return [LlmRegressionDrillResponse.model_validate(r.as_dict()) for r in _HARNESS.list_drills()]


@router.get("/drills/{drill_id}", response_model=LlmRegressionDrillResponse, dependencies=_AUTH)
async def get_llm_regression_drill(drill_id: str) -> LlmRegressionDrillResponse:
    row = _HARNESS.get_drill(drill_id)
    if row is None:
        raise HTTPException(status_code=404, detail="llm regression drill not found")
    return LlmRegressionDrillResponse.model_validate(row.as_dict())


@router.get(
    "/postmortems", response_model=list[LlmRegressionPostmortemResponse], dependencies=_AUTH
)
async def list_llm_regression_postmortems() -> list[LlmRegressionPostmortemResponse]:
    rows = _HARNESS.list_postmortems()
    return [LlmRegressionPostmortemResponse.model_validate(p.as_dict()) for p in rows]


def bind_harness(harness: MemLlmRegressionHarness) -> None:
    global _HARNESS  # noqa: PLW0603
    _HARNESS = harness
