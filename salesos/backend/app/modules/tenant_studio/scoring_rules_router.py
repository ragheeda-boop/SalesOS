"""STORY-10-04 — Tenant Studio Scoring Rules HTTP (CAP-085).

CRUD + evaluate with fail-safe platform-default fallback.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.scoring_rules import ScoringRuleError
from app.modules.tenant_studio.scoring_rules_store import (
    DEFAULT_SCORING_RULES_STORE,
    MemScoringRulesStore,
)

router = APIRouter(prefix="/studio/scoring-rules", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_SCORING_RULES_STORE


class BoostIn(BaseModel):
    field: str = Field(..., min_length=1, max_length=64)
    op: Literal["eq", "neq", "gte", "lte", "gt", "lt", "contains", "exists"]
    value: Any = None
    delta: float = 0.0


class ScoringRuleUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    target_type: Literal["lead", "company", "opportunity"]
    dimension_weights: dict[str, float] = Field(default_factory=dict)
    boosts: list[BoostIn] = Field(default_factory=list)
    active: bool = True


class ScoringRuleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    target_type: str
    dimension_weights: dict[str, float] = Field(default_factory=dict)
    boosts: list[dict[str, Any]] = Field(default_factory=list)
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


class ScoringEvaluateBody(BaseModel):
    target_type: Literal["lead", "company", "opportunity"]
    dimension_scores: dict[str, float] = Field(default_factory=dict)
    attributes: dict[str, Any] = Field(default_factory=dict)
    rule_id: str | None = None


class ScoringEvaluateResponse(BaseModel):
    score: float
    source: str
    fallback_used: bool = False
    fallback_reason: str | None = None
    rule_id: str | None = None
    explanation: list[str] = Field(default_factory=list)
    dimension_weights_used: dict[str, float] = Field(default_factory=dict)


@router.post("", response_model=ScoringRuleResponse, dependencies=_AUTH)
async def upsert_scoring_rule(
    body: ScoringRuleUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ScoringRuleResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            target_type=body.target_type,
            dimension_weights=dict(body.dimension_weights),
            boosts=[b.model_dump() for b in body.boosts],
            active=body.active,
            rule_id=body.id,
        )
    except ScoringRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return ScoringRuleResponse.model_validate(row.as_dict())


@router.get("", response_model=list[ScoringRuleResponse], dependencies=_AUTH)
async def list_scoring_rules(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[ScoringRuleResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [ScoringRuleResponse.model_validate(r.as_dict()) for r in rows]


@router.post(
    "/evaluate",
    response_model=ScoringEvaluateResponse,
    dependencies=_AUTH,
)
async def evaluate_scoring_rule(
    body: ScoringEvaluateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ScoringEvaluateResponse:
    try:
        result = _STORE.evaluate(
            tenant_id=str(tenant_id),
            target_type=body.target_type,
            dimension_scores=dict(body.dimension_scores),
            attributes=dict(body.attributes),
            rule_id=body.rule_id,
        )
    except ScoringRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ScoringEvaluateResponse.model_validate(result.as_dict())


@router.get("/{rule_id}", response_model=ScoringRuleResponse, dependencies=_AUTH)
async def get_scoring_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ScoringRuleResponse:
    row = _STORE.get(rule_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="scoring rule not found")
    return ScoringRuleResponse.model_validate(row.as_dict())


def bind_store(store: MemScoringRulesStore) -> None:
    """Test helper — swap process-local store."""
    global _STORE  # noqa: PLW0603
    _STORE = store
