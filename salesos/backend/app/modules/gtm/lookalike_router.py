"""STORY-11-04 — GTM Lookalike Accounts HTTP (CAP-098).

Versioned LookalikeModel from tenant won/lost Opportunity-shaped history.
Not Production GO. DEC-085 untouched.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.dependencies import get_current_tenant_id, verify_token
from app.modules.gtm.lookalike import LookalikeError
from app.modules.gtm.lookalike_store import (
    DEFAULT_LOOKALIKE_STORE,
    MemLookalikeStore,
)

router = APIRouter(prefix="/gtm/lookalikes", tags=["GTM Intelligence"])
_AUTH = [Depends(verify_token)]

_STORE = DEFAULT_LOOKALIKE_STORE


class LookalikeBody(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    company_name: str = Field(..., min_length=1, max_length=200)
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    limit: int = Field(default=10, ge=1, le=50)
    id: str | None = None


class LookalikeHitResponse(BaseModel):
    company_id: str
    company_name: str
    industry: str = ""
    city: str = ""
    employees_count: int | None = None
    similarity: float = 0.0
    outcome_affinity: str = ""
    matched_features: list[str] = Field(default_factory=list)


class LookalikeResponse(BaseModel):
    id: str
    tenant_id: str
    name: str
    seed: dict[str, Any]
    hits: list[LookalikeHitResponse]
    trained_on_won: int = 0
    trained_on_lost: int = 0
    schema_version: int = 1
    created_at: str = ""
    updated_at: str = ""
    hit_count: int = 0


@router.get("/meta", dependencies=_AUTH)
async def lookalike_meta() -> dict[str, Any]:
    return {
        "object": "LookalikeModel",
        "training": "tenant won/lost Opportunity-shaped history",
        "features": ["industry", "city", "employees_count"],
        "honesty": (
            "CI uses in-memory won/lost Opportunity fixtures; "
            "live Muhide Opportunity ML backtest / 141221 not claimed."
        ),
    }


@router.post("", response_model=LookalikeResponse, dependencies=_AUTH)
async def run_lookalikes(
    body: LookalikeBody,
    tenant_id: str = Depends(get_current_tenant_id),
) -> LookalikeResponse:
    try:
        row = _STORE.run(
            tenant_id=str(tenant_id),
            name=body.name,
            company_name=body.company_name,
            industry=body.industry or None,
            city=body.city or None,
            employees_count=body.employees_count,
            limit=body.limit,
            model_id=body.id,
        )
    except LookalikeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return LookalikeResponse.model_validate(row.as_dict())


@router.get("", response_model=list[LookalikeResponse], dependencies=_AUTH)
async def list_lookalikes(
    tenant_id: str = Depends(get_current_tenant_id),
) -> list[LookalikeResponse]:
    rows = _STORE.list_for_tenant(tenant_id=str(tenant_id))
    return [LookalikeResponse.model_validate(r.as_dict()) for r in rows]


@router.get("/{model_id}", response_model=LookalikeResponse, dependencies=_AUTH)
async def get_lookalike(
    model_id: str,
    tenant_id: str = Depends(get_current_tenant_id),
) -> LookalikeResponse:
    row = _STORE.get(model_id, tenant_id=str(tenant_id))
    if row is None:
        raise HTTPException(status_code=404, detail="lookalike model not found")
    return LookalikeResponse.model_validate(row.as_dict())


def bind_store(store: MemLookalikeStore) -> None:
    global _STORE  # noqa: PLW0603
    _STORE = store
