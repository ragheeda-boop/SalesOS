"""STORY-11-01 — GTM ICP Profile HTTP (CAP-095 / OBJ-350).

Versioned reusable ICPProfile CRUD + deterministic score.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.icp import ICPError
from app.modules.gtm.icp_store import DEFAULT_ICP_STORE, MemICPStore

router = APIRouter(prefix="/gtm/icp-profiles", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_ICP_STORE


class ICPWeightsBody(BaseModel):
    industry: float | None = None
    city: float | None = None
    employees: float | None = None
    titles: float | None = None
    keywords: float | None = None


class ICPProfileCreateBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str = ""
    industries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    employees_min: int | None = None
    employees_max: int | None = None
    titles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    weights: ICPWeightsBody | None = None
    id: str | None = None
    is_active: bool = True


class ICPProfileUpdateBody(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = None
    industries: list[str] | None = None
    cities: list[str] | None = None
    employees_min: int | None = None
    employees_max: int | None = None
    titles: list[str] | None = None
    keywords: list[str] | None = None
    weights: ICPWeightsBody | None = None
    is_active: bool | None = None


class ICPScoreBody(BaseModel):
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    title: str = ""
    name: str = ""
    description: str = ""
    keywords: str = ""
    notes: str = ""


class ICPProfileResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    description: str = ""
    criteria: dict[str, Any]
    weights: dict[str, Any]
    schema_version: int = 1
    is_active: bool = True
    created_at: str = ""
    updated_at: str = ""


class ICPScoreResponse(BaseModel):
    profile_id: str
    schema_version: int
    score: float
    max_score: float
    fit_ratio: float
    matched: dict[str, bool]
    company: dict[str, Any]


@router.get("/meta", dependencies=_AUTH)
async def icp_meta() -> dict[str, Any]:
    return {
        "object": "ICPProfile",
        "filters": [
            "industries",
            "cities",
            "employees_min",
            "employees_max",
            "titles",
            "keywords",
        ],
        "versioning": "schema_version increments on PUT",
        "scoring": "deterministic weighted fit (not ML backtest)",
        "honesty": (
            "In-memory tenant store for CI/pilot scaffolding; "
            "no historical won/lost Opportunity backtest claimed; "
            "live 141221 Postgres adapter not claimed."
        ),
    }


@router.post("", response_model=ICPProfileResponse, dependencies=_AUTH)
async def create_icp_profile(
    body: ICPProfileCreateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ICPProfileResponse:
    try:
        w = body.weights.model_dump(exclude_none=True) if body.weights else None
        row = _STORE.create(
            tenant_id=str(tenant_id),
            name=body.name,
            description=body.description,
            industries=list(body.industries),
            cities=list(body.cities),
            employees_min=body.employees_min,
            employees_max=body.employees_max,
            titles=list(body.titles),
            keywords=list(body.keywords),
            weights=w,
            profile_id=body.id,
            is_active=body.is_active,
        )
    except ICPError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ICPProfileResponse.model_validate(row.as_dict())


@router.get("", response_model=list[ICPProfileResponse], dependencies=_AUTH)
async def list_icp_profiles(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[ICPProfileResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [ICPProfileResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{profile_id}", response_model=ICPProfileResponse, dependencies=_AUTH)
async def get_icp_profile(
    profile_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ICPProfileResponse:
    row = _STORE.get(profile_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="icp profile not found")
    return ICPProfileResponse.model_validate(row.as_dict())


@router.put("/{profile_id}", response_model=ICPProfileResponse, dependencies=_AUTH)
async def update_icp_profile(
    profile_id: str,
    body: ICPProfileUpdateBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ICPProfileResponse:
    try:
        w = body.weights.model_dump(exclude_none=True) if body.weights else None
        row = _STORE.update(
            profile_id,
            tenant_id=str(tenant_id),
            name=body.name,
            description=body.description,
            industries=body.industries,
            cities=body.cities,
            employees_min=body.employees_min,
            employees_max=body.employees_max,
            titles=body.titles,
            keywords=body.keywords,
            weights=w,
            is_active=body.is_active,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="icp profile not found") from exc
    except ICPError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ICPProfileResponse.model_validate(row.as_dict())


@router.post(
    "/{profile_id}/score",
    response_model=ICPScoreResponse,
    dependencies=_AUTH,
)
async def score_icp_profile(
    profile_id: str,
    body: ICPScoreBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> ICPScoreResponse:
    try:
        result = _STORE.score(
            profile_id,
            tenant_id=str(tenant_id),
            company=body.model_dump(),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="icp profile not found") from exc
    except ICPError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return ICPScoreResponse.model_validate(result.as_dict())


def bind_store(store: MemICPStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
