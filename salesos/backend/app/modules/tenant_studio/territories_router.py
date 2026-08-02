"""STORY-10-05 — Tenant Studio Territories HTTP (CAP-087).

CRUD + assign over existing CAP-017 territory runtime (config surface only).
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.tenant_studio.territories import (
    VALID_MATCH_FIELDS,
    VALID_MATCH_OPS,
    TerritoryRuleError,
)
from app.modules.tenant_studio.territories_store import (
    DEFAULT_TERRITORIES_STORE,
    MemTerritoriesStore,
)

router = APIRouter(prefix="/studio/territories", tags=["Tenant Studio"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_TERRITORIES_STORE


class MatchConditionIn(BaseModel):
    field: str = Field(..., min_length=1, max_length=64)
    op: Literal["eq", "neq", "in", "contains", "gte", "lte", "gt", "lt"]
    value: Any = None


class TerritoryRuleUpsert(BaseModel):
    id: str | None = None
    name: str = Field(..., min_length=1, max_length=200)
    territory_key: str = Field(..., min_length=1, max_length=128)
    region: str = Field(default="", max_length=128)
    rep_id: str = Field(default="", max_length=128)
    priority: int = 100
    match_conditions: list[MatchConditionIn] = Field(default_factory=list)
    active: bool = True


class TerritoryRuleResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    territory_key: str
    region: str = ""
    rep_id: str = ""
    priority: int = 100
    match_conditions: list[dict[str, Any]] = Field(default_factory=list)
    active: bool = True
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""


class TerritoryAssignBody(BaseModel):
    attributes: dict[str, Any] = Field(default_factory=dict)
    rule_id: str | None = None


class TerritoryAssignResponse(BaseModel):
    matched: bool
    territory_key: str | None = None
    rule_id: str | None = None
    region: str = ""
    rep_id: str = ""
    source: str = "unmatched"
    explanation: list[str] = Field(default_factory=list)


@router.get("/meta", dependencies=_AUTH)
async def territories_meta() -> dict[str, Any]:
    """Field/op catalog for Studio FE (CAP-087)."""
    return {
        "match_fields": sorted(VALID_MATCH_FIELDS),
        "match_ops": sorted(VALID_MATCH_OPS),
        "dimensions": ["geography", "industry", "size"],
        "persistence": "memory",
        "runtime": "CAP-017",
        "policy_count_delta": 0,
    }


@router.post("", response_model=TerritoryRuleResponse, dependencies=_AUTH)
async def upsert_territory_rule(
    body: TerritoryRuleUpsert,
    tenant_id: str = Depends(get_current_tenant_id),
) -> TerritoryRuleResponse:
    try:
        row = _STORE.upsert(
            tenant_id=str(tenant_id),
            name=body.name,
            territory_key=body.territory_key,
            match_conditions=[c.model_dump() for c in body.match_conditions],
            region=body.region,
            rep_id=body.rep_id,
            priority=body.priority,
            active=body.active,
            rule_id=body.id,
        )
    except TerritoryRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return TerritoryRuleResponse.model_validate(row.as_dict())


@router.get("", response_model=list[TerritoryRuleResponse], dependencies=_AUTH)
async def list_territory_rules(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[TerritoryRuleResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [TerritoryRuleResponse.model_validate(r.as_dict()) for r in rows]


@router.post(
    "/assign",
    response_model=TerritoryAssignResponse,
    dependencies=_AUTH,
)
async def assign_territory_rule(
    body: TerritoryAssignBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> TerritoryAssignResponse:
    try:
        result = _STORE.assign(
            tenant_id=str(tenant_id),
            attributes=dict(body.attributes),
            rule_id=body.rule_id,
        )
    except TerritoryRuleError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TerritoryAssignResponse.model_validate(result.as_dict())


@router.get("/{rule_id}", response_model=TerritoryRuleResponse, dependencies=_AUTH)
async def get_territory_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> TerritoryRuleResponse:
    row = _STORE.get(rule_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="territory rule not found")
    return TerritoryRuleResponse.model_validate(row.as_dict())


@router.delete("/{rule_id}", dependencies=_AUTH)
async def delete_territory_rule(
    rule_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> dict[str, Any]:
    ok = _STORE.delete(rule_id, tenant_id=str(tenant_id))
    if not ok:
        raise HTTPException(status_code=404, detail="territory rule not found")
    return {"deleted": True, "id": rule_id}


def bind_store(store: MemTerritoriesStore) -> None:
    """Test helper — swap process-local store."""
    global _STORE  # noqa: PLW0603
    _STORE = store
