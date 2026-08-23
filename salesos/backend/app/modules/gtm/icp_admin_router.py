"""ICP profile admin API (Phase 4C) — tenant-scoped CRUD over PostgresICPRepository.

Gives PO/Data a supported path to populate real ICP profiles (the P1 data
action) without SQL access. All reads/writes pin the canonical app.tenant_id
GUC inside the repository; tenant identity always comes from auth, never from
the request body.
"""

import logging

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.common.rate_limit import rate_limit_dep
from app.dependencies import get_current_tenant_id
from app.modules.gtm.icp import ICPError
from app.modules.gtm.icp_persistence import PostgresICPRepository

logger = logging.getLogger(__name__)

router = APIRouter(dependencies=[Depends(rate_limit_dep("icp_admin", 60, 60))])

_REPO = PostgresICPRepository(None)


class ICPCriteriaIn(BaseModel):
    industries: list[str] = Field(default_factory=list)
    cities: list[str] = Field(default_factory=list)
    employees_min: int | None = Field(default=None, ge=0)
    employees_max: int | None = Field(default=None, ge=0)
    titles: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)


class ICPWeightsIn(BaseModel):
    industry: float | None = None
    city: float | None = None
    employees: float | None = None
    titles: float | None = None
    keywords: float | None = None


class ICPProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    criteria: ICPCriteriaIn = Field(default_factory=ICPCriteriaIn)
    weights: ICPWeightsIn | None = None
    is_active: bool = True


class ICPProfilePatch(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    criteria: ICPCriteriaIn | None = None
    weights: ICPWeightsIn | None = None
    is_active: bool | None = None


def _profile_out(p) -> dict:
    d = p.as_dict()
    return {
        "id": p.id,
        "tenant_id": p.tenant_id,
        "name": p.name,
        "description": p.description,
        "criteria": d["criteria"],
        "weights": d["weights"],
        "schema_version": p.schema_version,
        "is_active": p.is_active,
        "created_at": p.created_at,
        "updated_at": p.updated_at,
    }


def _split(payload: ICPProfileCreate | ICPProfilePatch) -> dict:
    """Criteria/weights kwargs only — name/description/is_active are handled
    explicitly per handler to avoid duplicate-kwarg collisions."""
    kwargs = {}
    crit = getattr(payload, "criteria", None)
    if crit is not None:
        kwargs.update(
            industries=crit.industries,
            cities=crit.cities,
            employees_min=crit.employees_min,
            employees_max=crit.employees_max,
            titles=crit.titles,
            keywords=crit.keywords,
        )
    w = getattr(payload, "weights", None)
    if w is not None:
        kwargs["weights"] = {k: v for k, v in w.model_dump().items() if v is not None}
    return kwargs


@router.get("/icp/profiles")
async def list_icp_profiles(
    tenant_id: str = Depends(get_current_tenant_id),
    active_only: bool = False,
):
    profiles = (
        await _REPO.list_active(tenant_id=tenant_id)
        if active_only
        else await _REPO.list_for_tenant(tenant_id=tenant_id)
    )
    return {"profiles": [_profile_out(p) for p in profiles], "count": len(profiles)}


@router.post("/icp/profiles", status_code=201)
async def create_icp_profile(
    payload: ICPProfileCreate,
    tenant_id: str = Depends(get_current_tenant_id),
):
    try:
        p = await _REPO.create(
            tenant_id=tenant_id,
            name=payload.name,
            description=payload.description,
            is_active=payload.is_active,
            **_split(payload),
        )
    except ICPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _profile_out(p)


@router.get("/icp/profiles/{profile_id}")
async def get_icp_profile(
    profile_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
):
    p = await _REPO.get(profile_id, tenant_id=tenant_id)
    if p is None:
        raise HTTPException(status_code=404, detail="ICP profile not found")
    return _profile_out(p)


@router.patch("/icp/profiles/{profile_id}")
async def update_icp_profile(
    profile_id: str,
    payload: ICPProfilePatch,
    tenant_id: str = Depends(get_current_tenant_id),
):
    patch = {
        k: v
        for k, v in {
            "name": payload.name,
            "description": payload.description,
            "is_active": payload.is_active,
            **_split(payload),
        }.items()
        if v is not None
    }
    if not patch:
        raise HTTPException(status_code=422, detail="empty patch")
    try:
        p = await _REPO.update(profile_id, tenant_id=tenant_id, **patch)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="ICP profile not found") from exc
    except ICPError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return _profile_out(p)
